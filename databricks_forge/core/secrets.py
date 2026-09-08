"""Secrets and environment variable management for Databricks Lakehouse."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

from databricks_forge.core.client import DatabricksClientError

logger = logging.getLogger(__name__)


def load_dotenv_file(path: Optional[Path | str] = None) -> Dict[str, str]:
    """Parses a .env file into a dictionary without requiring external dependencies."""
    env_path = Path(path or ".env").resolve()
    if not env_path.is_file():
        return {}

    env_vars: Dict[str, str] = {}
    content = env_path.read_text(encoding="utf-8")

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if match:
            key, val = match.group(1), match.group(2)
            # Remove enclosing quotes
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            env_vars[key] = val

    return env_vars


class DatabricksSecretsClient:
    """Client for Databricks Secrets REST API (/api/2.0/secrets/*)."""

    def __init__(self, host: str, token: str, timeout: int = 30):
        if not host:
            raise DatabricksClientError("Databricks host must be provided.")
        if not token:
            raise DatabricksClientError("Databricks token must be provided.")

        self.host = host.rstrip("/")
        if not self.host.startswith("http://") and not self.host.startswith("https://"):
            self.host = f"https://{self.host}"

        self.token = token
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "databricks-forge-cli/0.2.0",
        }

    def _url(self, endpoint: str) -> str:
        return f"{self.host}/{endpoint.lstrip('/')}"

    def list_scopes(self) -> List[Dict[str, Any]]:
        """Lists all secret scopes in the workspace."""
        url = self._url("/api/2.0/secrets/scopes/list")
        try:
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json().get("scopes", [])
        except requests.exceptions.RequestException as exc:
            raise DatabricksClientError(f"Failed to list secret scopes: {exc}") from exc

    def create_scope(self, scope: str, initial_manage_principal: str = "users") -> Dict[str, Any]:
        """Creates a new secret scope."""
        url = self._url("/api/2.0/secrets/scopes/create")
        payload = {"scope": scope, "initial_manage_principal": initial_manage_principal}
        try:
            resp = requests.post(url, headers=self.headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except requests.exceptions.HTTPError as exc:
            # If already exists (400 RESOURCE_ALREADY_EXISTS), treat as idempotent success
            if exc.response.status_code == 400 and "ALREADY_EXISTS" in exc.response.text:
                logger.info("Secret scope '%s' already exists.", scope)
                return {"status": "already_exists", "scope": scope}
            raise DatabricksClientError(f"Failed to create secret scope '{scope}': {exc.response.text}") from exc
        except requests.exceptions.RequestException as exc:
            raise DatabricksClientError(f"Failed to create secret scope '{scope}': {exc}") from exc

    def put_secret(self, scope: str, key: str, string_value: str) -> Dict[str, Any]:
        """Stores or updates a secret key-value pair in a scope."""
        url = self._url("/api/2.0/secrets/put")
        payload = {"scope": scope, "key": key, "string_value": string_value}
        try:
            resp = requests.post(url, headers=self.headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except requests.exceptions.RequestException as exc:
            raise DatabricksClientError(f"Failed to put secret '{key}' in scope '{scope}': {exc}") from exc

    def list_secrets(self, scope: str) -> List[Dict[str, Any]]:
        """Lists metadata (keys) for all secrets in a scope (values are never returned by API for security)."""
        url = self._url("/api/2.0/secrets/list")
        try:
            resp = requests.get(url, headers=self.headers, params={"scope": scope}, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json().get("secrets", [])
        except requests.exceptions.RequestException as exc:
            raise DatabricksClientError(f"Failed to list secrets in scope '{scope}': {exc}") from exc

    def delete_secret(self, scope: str, key: str) -> Dict[str, Any]:
        """Deletes a secret from a scope."""
        url = self._url("/api/2.0/secrets/delete")
        payload = {"scope": scope, "key": key}
        try:
            resp = requests.post(url, headers=self.headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except requests.exceptions.RequestException as exc:
            raise DatabricksClientError(f"Failed to delete secret '{key}' in scope '{scope}': {exc}") from exc


def sync_env_to_scope(
    env_path: Path | str,
    scope_name: str,
    client: DatabricksSecretsClient,
    ignore_keys: Optional[List[str]] = None
) -> List[str]:
    """Synchronizes variables from a local .env file into a Databricks Secret Scope."""
    env_vars = load_dotenv_file(env_path)
    if not env_vars:
        raise ValueError(f"No variables found in environment file: {env_path}")

    ignore = set(ignore_keys or ["DATABRICKS_HOST", "DATABRICKS_TOKEN", "PATH", "PYTHONPATH"])
    client.create_scope(scope_name)

    synced: List[str] = []
    for k, v in env_vars.items():
        if k in ignore or not v:
            continue
        client.put_secret(scope=scope_name, key=k.lower(), string_value=v)
        synced.append(k.lower())

    return synced
