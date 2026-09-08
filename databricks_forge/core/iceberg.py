"""Core Apache Iceberg & Delta UniForm (Universal Format) management module."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def build_enable_uniform_statements(table_name: str) -> List[str]:
    """Generates the DDL statements to enable Delta UniForm (Iceberg compatibility) on a Delta table.
    
    UniForm generates Apache Iceberg metadata (metadata.json and manifests) alongside
    standard Delta logs, allowing engines like Trino, Snowflake, AWS Athena, Presto,
    and DuckDB to read Delta tables natively without data duplication.
    """
    target = (
        f"delta.`{table_name}`"
        if ("/" in table_name or "\\" in table_name)
        else table_name
    )

    statements = [
        (
            f"ALTER TABLE {target} SET TBLPROPERTIES ("
            f"'delta.columnMapping.mode' = 'name', "
            f"'delta.universalFormat.enabledFormats' = 'iceberg')"
        ),
        f"OPTIMIZE {target}",
    ]
    return statements


def build_create_uniform_table_statement(
    table_name: str,
    schema_ddl: str,
    partition_cols: Optional[List[str]] = None,
) -> str:
    """Generates DDL to create a new Delta Lake table with UniForm Iceberg enabled."""
    target = (
        f"delta.`{table_name}`"
        if ("/" in table_name or "\\" in table_name)
        else table_name
    )
    partition_clause = f" PARTITIONED BY ({', '.join(partition_cols)})" if partition_cols else ""

    stmt = (
        f"CREATE TABLE IF NOT EXISTS {target} (\n"
        f"  {schema_ddl}\n"
        f") USING DELTA{partition_clause}\n"
        f"TBLPROPERTIES (\n"
        f"  'delta.columnMapping.mode' = 'name',\n"
        f"  'delta.universalFormat.enabledFormats' = 'iceberg'\n"
        f");"
    )
    return stmt


def build_iceberg_snapshots_query(table_name: str) -> str:
    """Generates the SQL query to inspect historical commits and snapshots of an Iceberg table."""
    return f"SELECT snapshot_id, committed_at, operation, summary FROM {table_name}.snapshots ORDER BY committed_at DESC"


def inspect_iceberg_plan(table_name: str) -> Dict[str, Any]:
    """Provides a structural inspection plan for an Iceberg or UniForm-enabled table."""
    return {
        "status": "PLANNED",
        "table": table_name,
        "uniform_statements": build_enable_uniform_statements(table_name),
        "snapshots_query": build_iceberg_snapshots_query(table_name),
        "iceberg_metadata_path": f"{table_name}/metadata/*.metadata.json",
        "supported_external_engines": [
            "Trino / Starburst",
            "Snowflake (External Iceberg Tables)",
            "AWS Athena",
            "DuckDB (iceberg extension)",
            "Apache Flink",
            "Presto",
        ],
    }
