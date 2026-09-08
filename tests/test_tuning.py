"""Tests for tuning module and forge tune CLI commands."""

from typer.testing import CliRunner
from databricks_forge.core.tuning import (
    TUNING_PROFILES,
    build_optimize_statement,
    build_vacuum_statement,
    execute_optimize,
    get_tuning_configs,
)
from databricks_forge.main import app

runner = CliRunner()


def test_build_optimize_statement_table_name():
    stmt = build_optimize_statement("events_silver")
    assert stmt == "OPTIMIZE events_silver"


def test_build_optimize_statement_with_zorder():
    stmt = build_optimize_statement("events_silver", ["user_id", "timestamp"])
    assert stmt == "OPTIMIZE events_silver ZORDER BY (user_id, timestamp)"


def test_build_optimize_statement_with_path():
    stmt = build_optimize_statement("/mnt/lakehouse/silver", ["date"])
    assert stmt == "OPTIMIZE delta.`/mnt/lakehouse/silver` ZORDER BY (date)"


def test_build_vacuum_statement():
    stmt = build_vacuum_statement("events_silver", 72)
    assert stmt == "VACUUM events_silver RETAIN 72 HOURS"

    stmt_path = build_vacuum_statement("/mnt/lakehouse/silver", 168)
    assert stmt_path == "VACUUM delta.`/mnt/lakehouse/silver` RETAIN 168 HOURS"


def test_get_tuning_configs_profiles():
    balanced = get_tuning_configs("balanced")
    assert balanced["spark.sql.adaptive.enabled"] == "true"
    assert balanced["spark.sql.adaptive.advisoryPartitionSizeInBytes"] == "67108864"

    write_heavy = get_tuning_configs("write_heavy")
    assert write_heavy["spark.sql.adaptive.advisoryPartitionSizeInBytes"] == "134217728"
    assert write_heavy["spark.sql.shuffle.partitions"] == "16"

    read_heavy = get_tuning_configs("read_heavy")
    assert read_heavy["spark.sql.adaptive.advisoryPartitionSizeInBytes"] == "33554432"


def test_execute_optimize_planned():
    result = execute_optimize("events_silver", ["user_id"])
    assert result["status"] == "PLANNED"
    assert result["statement"] == "OPTIMIZE events_silver ZORDER BY (user_id)"


def test_cli_tune_help():
    result = runner.invoke(app, ["tune", "--help"])
    assert result.exit_code == 0
    assert "optimize" in result.output
    assert "vacuum" in result.output
    assert "config" in result.output


def test_cli_tune_config_balanced():
    result = runner.invoke(app, ["tune", "config", "--profile", "balanced"])
    assert result.exit_code == 0
    assert "spark.sql.adaptive.enabled" in result.output
    assert "67108864" in result.output


def test_cli_tune_config_invalid():
    result = runner.invoke(app, ["tune", "config", "--profile", "invalid_profile"])
    assert result.exit_code != 0
    assert "Error" in result.output


def test_cli_tune_optimize():
    result = runner.invoke(app, ["tune", "optimize", "customers_gold", "--zorder", "customer_id,date"])
    assert result.exit_code == 0
    assert "OPTIMIZE customers_gold ZORDER BY (customer_id, date);" in result.output
    assert "spark.sql.adaptive.enabled" in result.output


def test_cli_tune_vacuum():
    result = runner.invoke(app, ["tune", "vacuum", "customers_gold", "--retention", "48"])
    assert result.exit_code == 0
    assert "VACUUM customers_gold RETAIN 48 HOURS;" in result.output
    assert "48 hours (2 days)" in result.output
