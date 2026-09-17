"""Unit tests for the Ollama client."""

import pytest
from unittest.mock import MagicMock, patch
from databricks_forge.ai.ollama_client import OllamaClient


def test_ollama_client_is_available():
    client = OllamaClient()

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        assert client.is_available() is True

    with patch("requests.get") as mock_get:
        mock_get.side_effect = Exception("Connection refused")
        assert client.is_available() is False


def test_ollama_list_models():
    client = OllamaClient()

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "models": [
                {"name": "llama3.2:3b"},
                {"name": "deepseek-r1:1.5b"},
            ]
        }
        models = client.list_models()
        assert models == ["llama3.2:3b", "deepseek-r1:1.5b"]


def test_ollama_chat_sync():
    client = OllamaClient()

    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "message": {"content": "Olá! Sou seu assistente de dados."}
        }
        reply = client.chat(
            model="llama3.2:3b",
            messages=[{"role": "user", "content": "Olá"}]
        )
        assert "Olá! Sou seu assistente de dados." in reply
