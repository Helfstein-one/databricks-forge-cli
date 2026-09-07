"""Tests for the Databricks Community Edition REST client."""

import base64
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch
from databricks_forge.core.client import DatabricksCEClient, DatabricksClientError


def test_client_init_validations():
    with pytest.raises(DatabricksClientError, match="host must be provided"):
        DatabricksCEClient(host="", token="token123")

    with pytest.raises(DatabricksClientError, match="token must be provided"):
        DatabricksCEClient(host="https://community.cloud.databricks.com", token="")

    client = DatabricksCEClient(host="community.cloud.databricks.com", token="my-token")
    assert client.host == "https://community.cloud.databricks.com"
    assert client.headers["Authorization"] == "Bearer my-token"


@patch("requests.get")
def test_client_verify_connection(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"object_type": "DIRECTORY"}
    mock_get.return_value = mock_resp

    client = DatabricksCEClient(host="https://community.cloud.databricks.com", token="my-token")
    res = client.verify_connection()

    assert res["status"] == "ok"
    mock_get.assert_called_once()


@patch("requests.post")
def test_client_mkdirs(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"{}"
    mock_resp.json.return_value = {}
    mock_post.return_value = mock_resp

    client = DatabricksCEClient(host="https://community.cloud.databricks.com", token="my-token")
    client.mkdirs("/Shared/test_dir")

    mock_post.assert_called_once_with(
        "https://community.cloud.databricks.com/api/2.0/workspace/mkdirs",
        headers=client.headers,
        json={"path": "/Shared/test_dir"},
        timeout=60,
    )


@patch("requests.post")
def test_client_upload_file(mock_post, tmp_path: Path):
    test_file = tmp_path / "sample.py"
    test_file.write_text("print('hello databricks')")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"{}"
    mock_resp.json.return_value = {}
    mock_post.return_value = mock_resp

    client = DatabricksCEClient(host="https://community.cloud.databricks.com", token="my-token")
    client.upload_file(
        local_path=test_file,
        remote_workspace_path="/Shared/sample",
    )

    # 2 calls: one for mkdirs (parent /Shared), one for import
    assert mock_post.call_count == 2
    import_call = mock_post.call_args_list[1]
    
    assert import_call[0][0] == "https://community.cloud.databricks.com/api/2.0/workspace/import"
    payload = import_call[1]["json"]
    assert payload["path"] == "/Shared/sample"
    assert payload["format"] == "SOURCE"
    assert payload["language"] == "PYTHON"
    
    decoded = base64.b64decode(payload["content"]).decode("utf-8")
    assert decoded == "print('hello databricks')"
