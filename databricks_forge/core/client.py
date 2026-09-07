"""Databricks REST API Client specialized for Community Edition and Workspace Operations."""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger(__name__)


class DatabricksClientError(Exception):
    """Base exception for Databricks client errors."""
    pass


class DatabricksCEClient:
    """Client for Databricks Community Edition REST API.
    
    Since Databricks Community Edition does not expose the Jobs API v2.1,
    the primary distribution mechanism is publishing compiled Wheel packages
    and Runner Notebooks to the Databricks Workspace via the Workspace API v2.0.
    """

    def __init__(self, host: str, token: str, timeout: int = 60):
        if not host:
            raise DatabricksClientError("Databricks host must be provided (e.g., https://community.cloud.databricks.com).")
        if not token:
            raise DatabricksClientError("Databricks personal access token must be provided.")

        self.host = host.rstrip("/")
        if not self.host.startswith("http://") and not self.host.startswith("https://"):
            self.host = f"https://{self.host}"

        self.token = token
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "databricks-forge-cli/0.1.0",
        }

    def _url(self, endpoint: str) -> str:
        clean_endpoint = endpoint.lstrip("/")
        return f"{self.host}/{clean_endpoint}"

    def verify_connection(self) -> Dict[str, Any]:
        """Validates that the host and token are valid by querying the workspace root."""
        url = self._url("/api/2.0/workspace/get-status")
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params={"path": "/"},
                timeout=self.timeout
            )
            response.raise_for_status()
            return {"status": "ok", "host": self.host}
        except requests.exceptions.HTTPError as exc:
            msg = f"Databricks API HTTP error ({exc.response.status_code}): {exc.response.text}"
            raise DatabricksClientError(msg) from exc
        except requests.exceptions.RequestException as exc:
            raise DatabricksClientError(f"Failed to connect to Databricks host {self.host}: {exc}") from exc

    def mkdirs(self, remote_workspace_path: str) -> Dict[str, Any]:
        """Creates the given directory and necessary parent directories in the workspace."""
        url = self._url("/api/2.0/workspace/mkdirs")
        payload = {"path": remote_workspace_path}
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as exc:
            raise DatabricksClientError(f"Failed to create workspace directory {remote_workspace_path}: {exc}") from exc

    def upload_file(
        self,
        local_path: Path | str,
        remote_workspace_path: str,
        file_format: Optional[str] = None,
        language: str = "PYTHON",
        overwrite: bool = True
    ) -> Dict[str, Any]:
        """Imports a file into the Databricks Workspace via /api/2.0/workspace/import.
        
        Args:
            local_path: Local path to the file (e.g. .whl or .py).
            remote_workspace_path: Target destination path in Databricks Workspace.
            file_format: SOURCE, HTML, JUPYTER, DBC, AUTO, or RAW.
            language: SCALA, PYTHON, SQL, or R (for SOURCE format).
            overwrite: Whether to overwrite existing destination.
        """
        path = Path(local_path)
        if not path.is_file():
            raise FileNotFoundError(f"Local file does not exist: {path}")

        # Ensure parent directory exists in workspace
        parent_dir = str(Path(remote_workspace_path).parent).replace("\\", "/")
        if parent_dir and parent_dir != "/":
            self.mkdirs(parent_dir)

        # Infer format if not specified
        if file_format is None:
            if path.suffix == ".py":
                file_format = "SOURCE"
            elif path.suffix == ".ipynb":
                file_format = "JUPYTER"
            elif path.suffix == ".dbc":
                file_format = "DBC"
            else:
                file_format = "AUTO"

        with open(path, "rb") as f:
            encoded_content = base64.b64encode(f.read()).decode("utf-8")

        url = self._url("/api/2.0/workspace/import")
        payload: Dict[str, Any] = {
            "path": remote_workspace_path,
            "format": file_format,
            "content": encoded_content,
            "overwrite": overwrite,
        }

        if file_format == "SOURCE":
            payload["language"] = language

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json() if response.content else {"status": "imported", "path": remote_workspace_path}
        except requests.exceptions.RequestException as exc:
            details = getattr(getattr(exc, "response", None), "text", str(exc))
            raise DatabricksClientError(f"Failed to import file to {remote_workspace_path}: {details}") from exc

    def list_status(self, remote_workspace_path: str) -> List[Dict[str, Any]]:
        """Lists objects in the workspace directory."""
        url = self._url("/api/2.0/workspace/list")
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params={"path": remote_workspace_path},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("objects", [])
        except requests.exceptions.RequestException as exc:
            raise DatabricksClientError(f"Failed to list workspace path {remote_workspace_path}: {exc}") from exc

    def delete_path(self, remote_workspace_path: str, recursive: bool = False) -> Dict[str, Any]:
        """Deletes an object or directory from the workspace."""
        url = self._url("/api/2.0/workspace/delete")
        payload = {"path": remote_workspace_path, "recursive": recursive}
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as exc:
            raise DatabricksClientError(f"Failed to delete workspace path {remote_workspace_path}: {exc}") from exc
