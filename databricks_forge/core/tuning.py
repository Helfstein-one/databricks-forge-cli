"""Core performance tuning and Delta Lake optimization engine."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

TUNING_PROFILES = {
    "balanced": {
        "spark.sql.adaptive.enabled": "true",
        "spark.sql.adaptive.coalescePartitions.enabled": "true",
        "spark.sql.adaptive.skewJoin.enabled": "true",
        "spark.sql.adaptive.localShuffleReader.enabled": "true",
        "spark.sql.adaptive.advisoryPartitionSizeInBytes": "67108864",  # 64MB
        "spark.databricks.delta.optimizeWrite.enabled": "true",
        "spark.databricks.delta.autoCompact.enabled": "true",
    },
    "write_heavy": {
        "spark.sql.adaptive.enabled": "true",
        "spark.sql.adaptive.coalescePartitions.enabled": "true",
        "spark.sql.adaptive.skewJoin.enabled": "true",
        "spark.sql.adaptive.advisoryPartitionSizeInBytes": "134217728",  # 128MB
        "spark.databricks.delta.optimizeWrite.enabled": "true",
        "spark.databricks.delta.autoCompact.enabled": "true",
        "spark.sql.shuffle.partitions": "16",
    },
    "read_heavy": {
        "spark.sql.adaptive.enabled": "true",
        "spark.sql.adaptive.coalescePartitions.enabled": "true",
        "spark.sql.adaptive.skewJoin.enabled": "true",
        "spark.sql.adaptive.localShuffleReader.enabled": "true",
        "spark.sql.adaptive.advisoryPartitionSizeInBytes": "33554432",  # 32MB
        "spark.databricks.delta.optimizeWrite.enabled": "false",
        "spark.databricks.delta.autoCompact.enabled": "false",
    },
}


def build_optimize_statement(
    table_name_or_path: str,
    zorder_columns: Optional[List[str]] = None,
) -> str:
    """Constructs the SQL OPTIMIZE statement for a Delta table."""
    target = (
        f"delta.`{table_name_or_path}`"
        if ("/" in table_name_or_path or "\\" in table_name_or_path)
        else table_name_or_path
    )
    stmt = f"OPTIMIZE {target}"
    if zorder_columns:
        cols = ", ".join(zorder_columns)
        stmt += f" ZORDER BY ({cols})"
    return stmt


def build_vacuum_statement(
    table_name_or_path: str,
    retention_hours: int = 168,
) -> str:
    """Constructs the SQL VACUUM statement for a Delta table."""
    target = (
        f"delta.`{table_name_or_path}`"
        if ("/" in table_name_or_path or "\\" in table_name_or_path)
        else table_name_or_path
    )
    return f"VACUUM {target} RETAIN {retention_hours} HOURS"


def get_tuning_configs(profile: str = "balanced") -> Dict[str, str]:
    """Returns Spark configuration key-values for a given performance profile."""
    return TUNING_PROFILES.get(profile, TUNING_PROFILES["balanced"])


def execute_optimize(
    table_name_or_path: str,
    zorder_columns: Optional[List[str]] = None,
    spark: Optional[Any] = None,
) -> Dict[str, Any]:
    """Executes Delta table optimization or returns the planned statement."""
    statement = build_optimize_statement(table_name_or_path, zorder_columns)
    
    if spark is not None:
        start = time.perf_counter()
        df = spark.sql(statement)
        metrics = df.collect()
        duration = round(time.perf_counter() - start, 3)
        row_dict = metrics[0].asDict() if metrics else {}
        return {
            "status": "SUCCESS",
            "statement": statement,
            "duration_seconds": duration,
            "metrics": row_dict,
        }

    return {
        "status": "PLANNED",
        "statement": statement,
        "table": table_name_or_path,
        "zorder": zorder_columns or [],
    }
