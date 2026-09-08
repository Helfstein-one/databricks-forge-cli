"""Unified Secrets Management for {{project_name}} Lakehouse.

Supports transparent switching between Databricks Secret Scopes (dbutils)
and Local / Container environment variables (.env).
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def get_secret(scope: str, key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieves a secret value transparently across runtime environments.
    
    Order of resolution:
    1. Databricks dbutils.secrets.get(scope, key) if running on a Databricks cluster.
    2. Environment variable matching exact KEY (uppercase or lowercase).
    3. Environment variable formatted as SCOPE_KEY (e.g. LAKEHOUSE_API_KEY).
    4. Default value if provided, or raises KeyError if none found.

    Args:
        scope: Databricks secret scope name.
        key: Secret key name within the scope.
        default: Fallback value if secret is not set.

    Returns:
        The secret string value.
    """
    # 1. Attempt Databricks dbutils
    try:
        # Check for active Databricks notebook / cluster environment
        import IPython
        dbutils = IPython.get_ipython().user_ns.get("dbutils")
        if dbutils and hasattr(dbutils, "secrets"):
            return dbutils.secrets.get(scope=scope, key=key)
    except Exception:
        pass

    # 2. Local Environment Variable resolution
    # Try exact key, lowercase, uppercase, and scope_key prefixes
    candidates = [
        key,
        key.upper(),
        key.lower(),
        f"{scope}_{key}".upper(),
        f"{scope}_{key}".lower(),
    ]

    for candidate in candidates:
        val = os.getenv(candidate)
        if val is not None:
            return val

    if default is not None:
        return default

    raise KeyError(
        f"Secret '{key}' not found in Databricks scope '{scope}' or local environment variables ({candidates})."
    )
