"""Delta Lake and Apache Spark Performance Tuning Module.

Provides automated tuning configurations for Spark AQE (Adaptive Query Execution),
Delta table file compaction (OPTIMIZE), multi-dimensional clustering (Z-ORDER),
and historical file pruning (VACUUM).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

try:
    from pyspark.sql import SparkSession
except ImportError:
    SparkSession = Any  # type: ignore

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


def apply_spark_tuning_defaults(
    spark: SparkSession, profile: str = "balanced"
) -> Dict[str, str]:
    """Applies recommended Spark AQE and Delta Lake tuning parameters to the session.
    
    Args:
        spark: Active SparkSession.
        profile: Tuning profile ('balanced', 'write_heavy', or 'read_heavy').
        
    Returns:
        Dictionary of applied Spark configuration keys and values.
    """
    configs = TUNING_PROFILES.get(profile, TUNING_PROFILES["balanced"])
    applied: Dict[str, str] = {}

    for key, value in configs.items():
        try:
            spark.conf.set(key, value)
            applied[key] = value
        except Exception as exc:
            logger.debug("Could not set configuration '%s': %s", key, exc)

    logger.info("Applied '%s' Spark tuning profile (%d configurations)", profile, len(applied))
    return applied


def optimize_delta_table(
    spark: SparkSession,
    table_name_or_path: str,
    zorder_columns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Runs OPTIMIZE and optional ZORDER BY on a Delta table to eliminate small files.
    
    Args:
        spark: Active SparkSession.
        table_name_or_path: Target Delta table identifier or file path.
        zorder_columns: Optional list of column names for multi-dimensional clustering.
        
    Returns:
        Optimization metrics dictionary (files added, files removed, bytes compacted).
    """
    target = (
        f"delta.`{table_name_or_path}`"
        if ("/" in table_name_or_path or "\\" in table_name_or_path)
        else table_name_or_path
    )

    query = f"OPTIMIZE {target}"
    if zorder_columns:
        cols_str = ", ".join(zorder_columns)
        query += f" ZORDER BY ({cols_str})"

    logger.info("Executing Delta optimization: %s", query)
    try:
        result_df = spark.sql(query)
        metrics = result_df.collect()
        if metrics:
            row_dict = metrics[0].asDict()
            logger.info("Delta optimization completed: %s", row_dict)
            return {
                "status": "SUCCESS",
                "table": table_name_or_path,
                "metrics": row_dict,
            }
        return {"status": "SUCCESS", "table": table_name_or_path, "metrics": {}}
    except Exception as exc:
        logger.error("Failed to execute OPTIMIZE on '%s': %s", table_name_or_path, exc)
        return {"status": "ERROR", "table": table_name_or_path, "error": str(exc)}


def vacuum_delta_table(
    spark: SparkSession,
    table_name_or_path: str,
    retention_hours: int = 168,
) -> Dict[str, Any]:
    """Runs VACUUM on a Delta table to safely remove obsolete historical snapshot files.
    
    Args:
        spark: Active SparkSession.
        table_name_or_path: Delta table name or path.
        retention_hours: Retention threshold in hours (default: 168 = 7 days).
        
    Returns:
        Vacuum execution result dictionary.
    """
    target = (
        f"delta.`{table_name_or_path}`"
        if ("/" in table_name_or_path or "\\" in table_name_or_path)
        else table_name_or_path
    )

    query = f"VACUUM {target} RETAIN {retention_hours} HOURS"
    logger.info("Executing Delta VACUUM: %s", query)
    try:
        spark.sql(query)
        return {
            "status": "SUCCESS",
            "table": table_name_or_path,
            "retention_hours": retention_hours,
        }
    except Exception as exc:
        logger.error("Failed to execute VACUUM on '%s': %s", table_name_or_path, exc)
        return {"status": "ERROR", "table": table_name_or_path, "error": str(exc)}
