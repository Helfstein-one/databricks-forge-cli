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
    assert "0.1.0" in result.output


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
    ])
    assert result.exit_code == 0
    assert "Successfully created" in result.output

    project_dir = tmp_path / "retail_lakehouse"
    assert project_dir.exists()
    assert (project_dir / "pyproject.toml").exists()
    assert (project_dir / "src/retail_lakehouse/session.py").exists()
    assert (project_dir / "notebooks/run_pipeline_notebook.py").exists()


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
