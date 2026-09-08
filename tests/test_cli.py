"""CLI end-to-end integration tests using Typer CliRunner."""

from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from databricks_forge.main import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "Databricks Forge CLI" in result.output
    assert "0.4.0" in result.output


def test_cli_check():
    result = runner.invoke(app, ["check"])
    assert result.exit_code == 0
    assert "Databricks Forge Diagnostics" in result.output
    assert "Python" in result.output


def test_cli_init_command(tmp_path: Path):
    result = runner.invoke(app, [
        "init",
        "retail_lakehouse",
        "--output-dir",
        str(tmp_path),
        "--description",
        "Test retail lakehouse pipeline",
        "--cloud",
        "aws",
        "--node-type",
        "i3.xlarge",
        "--workers",
        "2",
    ])
    assert result.exit_code == 0
    assert "Successfully created" in result.output
    # Check ASCII banner presence
    assert "DATABRICKS FORGE CLI" in result.output

    project_dir = tmp_path / "retail_lakehouse"
    assert project_dir.exists()
    assert (project_dir / "pyproject.toml").exists()
    assert (project_dir / "workflow.yaml").exists()
    assert (project_dir / "sql/01_clean_transactions.sql").exists()
    assert (project_dir / "sql/02_gold_metrics.sql").exists()
    assert (project_dir / "notebooks/master_dag_runner.py").exists()
    assert (project_dir / "src/retail_lakehouse/session.py").exists()
    assert (project_dir / "notebooks/run_pipeline_notebook.py").exists()

    # Check workflow.yaml has configured compute
    wf_content = (project_dir / "workflow.yaml").read_text()
    assert 'cloud: "aws"' in wf_content
    assert 'node_type_id: "i3.xlarge"' in wf_content
    assert "num_workers: 2" in wf_content


def test_cli_init_fails_if_dir_exists_and_not_empty(tmp_path: Path):
    existing = tmp_path / "existing_proj"
    existing.mkdir()
    (existing / "file.txt").write_text("content")

    result = runner.invoke(app, [
        "init",
        "existing_proj",
        "--output-dir",
        str(tmp_path),
    ])
    assert result.exit_code == 1
    normalized = " ".join(result.output.split())
    assert "already exists and is not empty" in normalized


def test_cli_compute_list():
    result = runner.invoke(app, ["compute", "list", "--cloud", "aws"])
    assert result.exit_code == 0
    assert "i3.xlarge" in result.output
    assert "Storage Optimized" in result.output


def test_cli_dag_validate(tmp_path: Path):
    # Scaffold a project first
    runner.invoke(app, ["init", "test_dag_proj", "--output-dir", str(tmp_path)])
    wf_file = tmp_path / "test_dag_proj" / "workflow.yaml"

    result = runner.invoke(app, ["dag", "validate", "--file", str(wf_file)])
    assert result.exit_code == 0
    assert "DAG Validation: OK" in result.output
    assert "Topological Execution Plan" in result.output


def test_cli_sql_deploy(tmp_path: Path):
    sql_file = tmp_path / "test.sql"
    sql_file.write_text("SELECT 1;")

    with patch("databricks_forge.main.DatabricksCEClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        result = runner.invoke(app, [
            "sql", "deploy", str(sql_file),
            "--target-path", "/Shared/sql/test",
            "--host", "https://community.cloud.databricks.com",
            "--token", "dapi_fake",
        ])
        assert result.exit_code == 0
        assert "deployed to /Shared/sql/test" in result.output


def test_cli_run_notebook():
    result = runner.invoke(app, [
        "run-notebook",
        "--target-path",
        "/Shared/test_pipeline",
        "--host",
        "https://community.cloud.databricks.com",
    ])
    assert result.exit_code == 0
    assert "Direct Notebook URL:" in result.output
    cleaned_output = result.output.replace("\n", "").replace(" ", "").replace("│", "")
    assert "https://community.cloud.databricks.com#workspace/Shared/test_pipeline/run_pipeline_notebook" in cleaned_output


@patch("databricks_forge.main.DatabricksCEClient")
@patch("databricks_forge.main.build_project_wheel")
def test_cli_deploy(mock_build, mock_client_cls, tmp_path: Path):
    dummy_wheel = tmp_path / "retail_lakehouse-0.1.0-py3-none-any.whl"
    dummy_wheel.write_text("binary content")
    mock_build.return_value = dummy_wheel

    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.host = "https://community.cloud.databricks.com"

    result = runner.invoke(app, [
        "deploy",
        "--host", "https://community.cloud.databricks.com",
        "--token", "test-token-123",
        "--target-path", "/Shared/deploy_test",
        "--project-dir", str(tmp_path),
    ])

    assert result.exit_code == 0
    assert "Deployment to Databricks CE Succeeded!" in result.output
    mock_client.verify_connection.assert_called_once()
    mock_client.upload_file.assert_called()
