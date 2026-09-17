"""Unit tests for the Semantic AI Agent."""

import pytest
from unittest.mock import MagicMock, patch
from databricks_forge.ai.agent import SemanticAgent
from databricks_forge.semantic.registry import SemanticRegistry
from databricks_forge.semantic.models import SemanticSchema, Entity


def test_agent_intent_classification():
    agent = SemanticAgent()

    assert agent.is_etl_request("Crie um etl para limpar bronze e salvar em silver") is True
    assert agent.is_etl_request("Gere um pipeline PySpark") is True
    assert agent.is_etl_request("Qual a média de vendas por produto?") is False

    assert agent.is_diagram_request("Gere o diagrama ERD das tabelas") is True
    assert agent.is_diagram_request("Mostre a linhagem Medallion") is True
    assert agent.is_diagram_request("Faça um SELECT na tabela silver") is False


def test_agent_process_diagram_request():
    agent = SemanticAgent()
    res = agent.process_message("Mostre o diagrama ERD das tabelas")

    assert res["type"] == "diagram"
    assert "erDiagram" in res["text"]
    assert res["mermaid"] is not None


from databricks_forge.ai.ollama_client import OllamaClient


@patch.object(OllamaClient, "is_available", return_value=False)
def test_agent_process_etl_proposal(mock_avail):
    agent = SemanticAgent()
    res = agent.process_message("Crie um etl PySpark para carregar bronze_raw_transactions em silver_transactions")

    assert res["type"] == "etl_proposal"
    assert "def run_pipeline" in res["code"]
    assert res["mermaid"] is not None
    assert "pipeline_name" in res
