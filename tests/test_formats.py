"""Tests for multi-format detection, planning, and CLI commands."""

from pathlib import Path
from typer.testing import CliRunner
from databricks_forge.core.formats import (
    SUPPORTED_FORMATS,
    build_convert_plan,
    detect_format_from_path,
)
from databricks_forge.main import app

runner = CliRunner()


def test_detect_format_from_path():
    assert detect_format_from_path("data/raw/transactions.parquet") == "parquet"
    assert detect_format_from_path("data/raw/transactions.orc") == "orc"
    assert detect_format_from_path("data/raw/events.avro") == "avro"
    assert detect_format_from_path("data/raw/users.csv") == "csv"
    assert detect_format_from_path("data/raw/users.tsv") == "csv"
    assert detect_format_from_path("data/raw/payload.json") == "json"
    assert detect_format_from_path("data/raw/payload.jsonl") == "json"
    assert detect_format_from_path("data/silver/table.delta") == "delta"
    assert detect_format_from_path("data/silver/_delta_log") == "delta"
    assert detect_format_from_path("iceberg_warehouse/db/table") == "iceberg"


def test_build_convert_plan():
    plan = build_convert_plan(
        source="raw/events.csv",
        target="silver/events_delta",
        from_format="csv",
        to_format="delta",
        partition_by=["date", "region"],
    )
    assert plan["source_format"] == "csv"
    assert plan["target_format"] == "delta"
    assert plan["partition_by"] == ["date", "region"]
    assert "spark.read.format('csv')" in plan["command_preview"]
    assert ".write.format('delta')" in plan["command_preview"]


def test_build_convert_plan_unsupported_format():
    import pytest
    with pytest.raises(ValueError, match="Unsupported source format"):
        build_convert_plan("data.xyz", "data.delta", from_format="xyz")


def test_cli_data_help():
    result = runner.invoke(app, ["data", "--help"])
    assert result.exit_code == 0
    assert "convert" in result.output
    assert "inspect" in result.output


def test_cli_data_convert():
    result = runner.invoke(
        app,
        ["data", "convert", "raw/input.parquet", "silver/target", "--to", "delta", "-p", "date"],
    )
    assert result.exit_code == 0
    assert "Multi-Format Conversion Plan" in result.output
    assert "PARQUET" in result.output
    assert "DELTA" in result.output
    assert "date" in result.output


def test_cli_data_inspect(tmp_path: Path):
    sample_file = tmp_path / "sample.parquet"
    sample_file.write_text("dummy content")

    result = runner.invoke(app, ["data", "inspect", str(sample_file)])
    assert result.exit_code == 0
    assert "PARQUET" in result.output
    assert "Single File" in result.output
