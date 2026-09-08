"""Tests for Databricks Secrets and environment variable management."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from typer.testing import CliRunner

from databricks_forge.core.secrets import (
    DatabricksSecretsClient,
    load_dotenv_file,
    sync_env_to_scope,
)
from databricks_forge.main import app

runner = CliRunner()


def test_load_dotenv_file(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("""
    # Comment line
    DB_USER=lakehouse_admin
    DB_PASSWORD="super_secret_password"
    API_KEY='12345-token'
    EMPTY_VAR=
    SPARK_DRIVER_MEMORY=4g
    """)

    env = load_dotenv_file(env_file)
    assert env["DB_USER"] == "lakehouse_admin"
    assert env["DB_PASSWORD"] == "super_secret_password"
    assert env["API_KEY"] == "12345-token"
    assert env["EMPTY_VAR"] == ""
    assert env["SPARK_DRIVER_MEMORY"] == "4g"


@patch("requests.get")
def test_secrets_client_list_scopes(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"scopes": [{"name": "app_scope", "backend_type": "DATABRICKS"}]}
    mock_get.return_value = mock_resp

    client = DatabricksSecretsClient(host="https://community.cloud.databricks.com", token="my-token")
    scopes = client.list_scopes()
    assert len(scopes) == 1
    assert scopes[0]["name"] == "app_scope"


@patch("requests.post")
def test_secrets_client_put_secret(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"{}"
    mock_resp.json.return_value = {}
    mock_post.return_value = mock_resp

    client = DatabricksSecretsClient(host="https://community.cloud.databricks.com", token="my-token")
    client.put_secret(scope="my_scope", key="api_key", string_value="secret_val")

    mock_post.assert_called_once_with(
        "https://community.cloud.databricks.com/api/2.0/secrets/put",
        headers=client.headers,
        json={"scope": "my_scope", "key": "api_key", "string_value": "secret_val"},
        timeout=30,
    )


def test_sync_env_to_scope(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("""
    DATABRICKS_HOST=https://community.cloud.databricks.com
    DATABRICKS_TOKEN=dapi_token
    APP_SECRET=topsecret123
    DB_HOST=10.0.0.1
    """)

    mock_client = MagicMock()

    synced = sync_env_to_scope(env_path=env_file, scope_name="prod_scope", client=mock_client)

    mock_client.create_scope.assert_called_once_with("prod_scope")
    # DATABRICKS_HOST and DATABRICKS_TOKEN are filtered out
    assert "app_secret" in synced
    assert "db_host" in synced
    assert "databricks_host" not in synced


def test_cli_secret_list():
    with patch("databricks_forge.main.DatabricksSecretsClient") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.list_scopes.return_value = [{"name": "finance_scope", "backend_type": "DATABRICKS"}]
        mock_cls.return_value = mock_instance

        result = runner.invoke(app, [
            "secret", "list",
            "--host", "https://community.cloud.databricks.com",
            "--token", "dapi_test",
        ])
        assert result.exit_code == 0
        assert "finance_scope" in result.output


def test_cli_secret_set():
    with patch("databricks_forge.main.DatabricksSecretsClient") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance

        result = runner.invoke(app, [
            "secret", "set", "prod_scope", "database_pwd",
            "--value", "mypassword123",
            "--host", "https://community.cloud.databricks.com",
            "--token", "dapi_test",
        ])
        assert result.exit_code == 0
        assert "saved successfully" in result.output
        mock_instance.put_secret.assert_called_once_with(
            scope="prod_scope", key="database_pwd", string_value="mypassword123"
        )
