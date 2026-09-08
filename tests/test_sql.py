"""Tests for SQL job module and workspace deployment."""

from pathlib import Path
from unittest.mock import MagicMock
import pytest
from databricks_forge.core.sql import (
    split_sql_statements,
    deploy_sql_to_workspace,
    SQLJobError,
)


def test_split_sql_statements():
    raw_sql = """
    -- This is a comment
    SELECT * FROM bronze_table;
    
    /* Multi line 
       comment */
    CREATE TABLE silver_table AS SELECT * FROM bronze_table;
    """
    stmts = split_sql_statements(raw_sql)
    assert len(stmts) == 2
    assert "SELECT * FROM bronze_table" in stmts[0]
    assert "CREATE TABLE silver_table" in stmts[1]


def test_deploy_sql_to_workspace(tmp_path: Path):
    sql_file = tmp_path / "transform.sql"
    sql_file.write_text("SELECT 1;")

    mock_client = MagicMock()
    mock_client.upload_file.return_value = {"status": "ok"}

    deploy_sql_to_workspace(sql_file, mock_client, "/Shared/sql/transform.sql")

    mock_client.upload_file.assert_called_once_with(
        local_path=sql_file,
        remote_workspace_path="/Shared/sql/transform",
        file_format="SOURCE",
        language="SQL",
        overwrite=True,
    )
