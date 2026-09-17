"""Unit tests for the OpenWebUI FastAPI Backend Server."""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from databricks_forge.ui.server import create_app
from databricks_forge.ai.ollama_client import OllamaClient


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_server_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@patch.object(OllamaClient, "is_available", return_value=True)
@patch.object(OllamaClient, "list_models", return_value=["llama3.2:3b", "deepseek-r1:1.5b"])
def test_server_models_online(mock_list, mock_avail, client):
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "llama3.2:3b" in data["models"]
    assert data["default_model"] == "llama3.2:3b"


@patch.object(OllamaClient, "is_available", return_value=False)
def test_server_models_offline(mock_avail, client):
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "offline"
    assert data["models"] == []


def test_server_catalog(client):
    response = client.get("/api/catalog")
    assert response.status_code == 200
    data = response.json()
    assert "entities" in data
    assert "erd_mermaid" in data
    assert "lineage_mermaid" in data
    assert "erDiagram" in data["erd_mermaid"]


def test_server_chat_stream_diagram(client):
    response = client.post(
        "/api/chat/stream",
        json={"message": "Mostre o diagrama ERD das tabelas", "model": "llama3.2:3b"},
    )
    assert response.status_code == 200
    text = response.text
    assert "event: message" in text
    assert "erDiagram" in text
    assert "event: done" in text


@patch.object(OllamaClient, "is_available", return_value=False)
def test_server_chat_stream_etl_proposal(mock_avail, client):
    response = client.post(
        "/api/chat/stream",
        json={"message": "Crie um etl PySpark para limpar bronze_raw_transactions", "model": "llama3.2:3b"},
    )
    assert response.status_code == 200
    text = response.text
    assert "etl_proposal" in text
    assert "def run_pipeline" in text


def test_server_approve_etl(client, tmp_path):
    with patch("databricks_forge.ai.etl_agent.ETLAgent.save_pipeline_files") as mock_save, \
         patch("databricks_forge.core.git_ops.GitOpsManager.commit_and_push") as mock_git:
        mock_save.return_value = {
            "pipeline_file": "/tmp/notebooks/clean_pipeline.py",
            "workflow_file": "/tmp/workflow.yaml",
        }
        mock_git.return_value = {
            "success": True,
            "commit_hash": "a1b2c3d",
            "branch": "main",
        }

        response = client.post(
            "/api/etl/approve",
            json={
                "pipeline_name": "clean_pipeline",
                "code": "print('clean')",
                "run_databricks": False,
                "push_git": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["commit_hash"] == "a1b2c3d"
        assert data["branch"] == "main"


def test_openai_compatibility_models(client):
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    model_ids = [m["id"] for m in data["data"]]
    assert "databricks-forge" in model_ids


def test_openai_compatibility_chat_completions(client):
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "databricks-forge",
            "messages": [{"role": "user", "content": "Mostre o diagrama ERD"}],
            "stream": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "chat.completion"
    assert "erDiagram" in data["choices"][0]["message"]["content"]
