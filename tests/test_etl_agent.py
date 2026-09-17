"""Unit tests for the ETL Agent and Git Operations."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from databricks_forge.ai.etl_agent import ETLAgent
from databricks_forge.core.git_ops import GitOpsManager
from databricks_forge.core.workflow import DAGWorkflow


from databricks_forge.ai.ollama_client import OllamaClient


@patch.object(OllamaClient, "is_available", return_value=False)
def test_etl_agent_generate_code(mock_avail):
    agent = ETLAgent()
    code = agent.generate_pipeline_code(
        prompt="Limpe a tabela bronze_orders e deduplique para silver_orders",
        source_table="bronze_orders",
        target_table="silver_orders",
        pipeline_name="clean_orders"
    )

    assert "def run_pipeline" in code
    assert "@pipeline_audit_step" in code
    assert 'spark.table("bronze_orders")' in code
    assert 'saveAsTable("silver_orders")' in code
    assert 'format("delta")' in code
    assert "dropDuplicates()" in code


@patch.object(OllamaClient, "is_available", return_value=False)
def test_etl_agent_save_pipeline_and_update_dag(mock_avail, tmp_path: Path):
    agent = ETLAgent(base_dir=tmp_path)
    wf_file = tmp_path / "workflow.yaml"

    code = agent.generate_pipeline_code(
        prompt="Test ETL",
        source_table="bronze_t",
        target_table="silver_t",
        pipeline_name="step_silver"
    )

    res = agent.save_pipeline_files(
        pipeline_name="step_silver",
        code=code,
        workflow_path=wf_file
    )

    pipeline_path = Path(res["pipeline_file"])
    assert pipeline_path.exists()
    assert wf_file.exists()

    # Validate resulting DAG with DAGWorkflow
    dag = DAGWorkflow.from_yaml(wf_file)
    assert len(dag.tasks) == 1
    assert dag.tasks[0].name == "step_silver"


def test_etl_agent_mermaid_pipeline():
    agent = ETLAgent()
    mermaid = agent.to_mermaid_pipeline("clean_pipeline", "bronze_raw", "silver_clean")
    assert "graph LR" in mermaid
    assert "bronze_raw" in mermaid
    assert "silver_clean" in mermaid


def test_git_ops_manager(tmp_path: Path):
    git_ops = GitOpsManager(repo_dir=tmp_path)

    with patch.object(git_ops, "_run_git") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="main\n")
        branch = git_ops.get_current_branch()
        assert branch == "main"

    with patch.object(git_ops, "_run_git") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="true\n")
        assert git_ops.is_git_repo() is True
