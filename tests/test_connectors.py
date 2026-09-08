"""Tests for database connectors catalog, URL building, and CLI commands."""

import pytest
from unittest.mock import patch
from typer.testing import CliRunner
from databricks_forge.core.connectors import (
    DATABASE_CATALOG,
    build_export_plan,
    build_ingest_plan,
    build_jdbc_url,
    check_db_connectivity,
    get_connector_info,
)
from databricks_forge.main import app

runner = CliRunner()


def test_database_catalog_contains_standard_engines():
    expected_engines = {
        "postgresql",
        "mysql",
        "sqlserver",
        "oracle",
        "snowflake",
        "mongodb",
        "bigquery",
        "sqlite",
    }
    assert expected_engines.issubset(set(DATABASE_CATALOG.keys()))


def test_get_connector_info():
    pg = get_connector_info("postgresql")
    assert pg["default_port"] == 5432
    assert pg["driver_class"] == "org.postgresql.Driver"

    with pytest.raises(ValueError, match="Unsupported database connector"):
        get_connector_info("unknown_db")


def test_build_jdbc_url():
    pg_url = build_jdbc_url("postgresql", host="db.internal", database="sales", port=5433)
    assert pg_url == "jdbc:postgresql://db.internal:5433/sales"

    mysql_url = build_jdbc_url("mysql", host="mysql.internal", database="crm")
    assert mysql_url == "jdbc:mysql://mysql.internal:3306/crm"

    sqlite_url = build_jdbc_url("sqlite", host="", database="/tmp/data.db")
    assert sqlite_url == "jdbc:sqlite:/tmp/data.db"


def test_build_ingest_plan():
    plan = build_ingest_plan(
        db_type="postgresql",
        source_table="customers",
        target_delta_table="customers_bronze",
        host="localhost",
        database="production",
        partition_column="customer_id",
        num_partitions=8,
    )
    assert plan["database_type"] == "postgresql"
    assert plan["source_table"] == "customers"
    assert plan["target_delta_table"] == "customers_bronze"
    assert plan["partition_column"] == "customer_id"
    assert plan["num_partitions"] == 8
    assert "partitionColumn" in plan["code_preview"]
    assert "customers_bronze" in plan["code_preview"]


def test_build_export_plan():
    plan = build_export_plan(
        source_delta_table="gold_sales",
        db_type="mysql",
        target_table="sales_reporting",
        host="reporting.internal",
        database="dw",
        mode="overwrite",
        batchsize=2000,
    )
    assert plan["source_delta_table"] == "gold_sales"
    assert plan["target_table"] == "sales_reporting"
    assert plan["mode"] == "overwrite"
    assert plan["batchsize"] == 2000
    assert "sales_reporting" in plan["code_preview"]


def test_check_db_connectivity_sqlite():
    result = check_db_connectivity("sqlite", host="localhost")
    assert result["status"] == "SUCCESS"
    assert "local file-based" in result["message"]


def test_check_db_connectivity_socket():
    with patch("socket.create_connection") as mock_conn:
        mock_conn.return_value.__enter__.return_value = None
        result = check_db_connectivity("postgresql", host="localhost", port=5432)
        assert result["status"] == "SUCCESS"
        assert result["port"] == 5432


def test_cli_connector_help():
    result = runner.invoke(app, ["connector", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output
    assert "test-connection" in result.output
    assert "plan-ingest" in result.output
    assert "plan-export" in result.output


def test_cli_connector_list():
    result = runner.invoke(app, ["connector", "list"])
    assert result.exit_code == 0
    assert "PostgreSQL" in result.output
    assert "MySQL" in result.output
    assert "Snowflake" in result.output
    assert "MongoDB" in result.output


def test_cli_connector_test_connection_sqlite():
    result = runner.invoke(app, ["connector", "test-connection", "sqlite"])
    assert result.exit_code == 0
    assert "Connection Successful" in result.output


def test_cli_connector_plan_ingest():
    result = runner.invoke(
        app,
        [
            "connector",
            "plan-ingest",
            "postgresql",
            "orders",
            "orders_bronze",
            "--database",
            "sales_db",
            "--partition-by",
            "order_id",
        ],
    )
    assert result.exit_code == 0
    assert "High-Performance Database Ingestion Plan" in result.output
    assert "orders_bronze" in result.output
    assert "order_id" in result.output


def test_cli_connector_plan_export():
    result = runner.invoke(
        app,
        [
            "connector",
            "plan-export",
            "gold_daily_kpis",
            "sqlserver",
            "daily_kpis",
            "--database",
            "finance_dw",
        ],
    )
    assert result.exit_code == 0
    assert "Reverse-ETL Export Plan" in result.output
    assert "daily_kpis" in result.output
