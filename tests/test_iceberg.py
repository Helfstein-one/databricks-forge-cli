"""Tests for Apache Iceberg and Delta UniForm integration and CLI commands."""

from typer.testing import CliRunner
from databricks_forge.core.iceberg import (
    build_create_uniform_table_statement,
    build_enable_uniform_statements,
    build_iceberg_snapshots_query,
    inspect_iceberg_plan,
)
from databricks_forge.main import app

runner = CliRunner()


def test_build_enable_uniform_statements():
    stmts = build_enable_uniform_statements("transactions_silver")
    assert len(stmts) == 2
    assert "delta.universalFormat.enabledFormats" in stmts[0]
    assert "delta.columnMapping.mode" in stmts[0]
    assert "OPTIMIZE transactions_silver" in stmts[1]


def test_build_create_uniform_table_statement():
    stmt = build_create_uniform_table_statement(
        table_name="gold_sales",
        schema_ddl="id STRING, amount DOUBLE, date DATE",
        partition_cols=["date"],
    )
    assert "CREATE TABLE IF NOT EXISTS gold_sales" in stmt
    assert "PARTITIONED BY (date)" in stmt
    assert "'delta.universalFormat.enabledFormats' = 'iceberg'" in stmt


def test_build_iceberg_snapshots_query():
    query = build_iceberg_snapshots_query("transactions_silver")
    assert "FROM transactions_silver.snapshots" in query
    assert "snapshot_id" in query


def test_inspect_iceberg_plan():
    plan = inspect_iceberg_plan("customers_silver")
    assert plan["table"] == "customers_silver"
    assert "Trino / Starburst" in plan["supported_external_engines"]
    assert "Snowflake (External Iceberg Tables)" in plan["supported_external_engines"]


def test_cli_iceberg_help():
    result = runner.invoke(app, ["iceberg", "--help"])
    assert result.exit_code == 0
    assert "enable-uniform" in result.output
    assert "inspect" in result.output
    assert "snapshots" in result.output


def test_cli_iceberg_enable_uniform():
    result = runner.invoke(app, ["iceberg", "enable-uniform", "sales_silver"])
    assert result.exit_code == 0
    assert "Delta UniForm (Apache Iceberg) Configuration" in result.output
    assert "delta.universalFormat.enabledFormats" in result.output
    assert "sales_silver" in result.output


def test_cli_iceberg_inspect():
    result = runner.invoke(app, ["iceberg", "inspect", "sales_silver"])
    assert result.exit_code == 0
    assert "Apache Iceberg Table Inspection" in result.output
    assert "Snowflake (External Iceberg Tables)" in result.output


def test_cli_iceberg_snapshots():
    result = runner.invoke(app, ["iceberg", "snapshots", "sales_silver"])
    assert result.exit_code == 0
    assert "Iceberg Snapshots & Commit History" in result.output
    assert "sales_silver.snapshots" in result.output
