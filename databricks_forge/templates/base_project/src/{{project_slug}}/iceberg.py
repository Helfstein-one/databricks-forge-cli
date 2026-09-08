"""Apache Iceberg and Delta UniForm (Universal Format) Integration Module.

Enables seamless interoperability between Delta Lake and Apache Iceberg ecosystems:
1. Delta UniForm: Generates Iceberg metadata alongside Delta logs on write,
   allowing Trino, Snowflake, AWS Athena, and DuckDB to read tables with zero data duplication.
2. Native Iceberg: Read and write native Iceberg tables via Spark Iceberg catalog with time-travel.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

try:
    from pyspark.sql import DataFrame, SparkSession
except ImportError:
    class DataFrame:  # type: ignore
        pass

    class SparkSession:  # type: ignore
        pass

logger = logging.getLogger(__name__)


def enable_delta_uniform(spark: SparkSession, table_name: str) -> Dict[str, Any]:
    """Enables Delta UniForm (Iceberg compatibility) on an existing Delta Lake table.
    
    Args:
        spark: Active SparkSession.
        table_name: Delta table name or file path.
        
    Returns:
        Execution status and details dictionary.
    """
    target = (
        f"delta.`{table_name}`"
        if ("/" in table_name or "\\" in table_name)
        else table_name
    )

    ddl_properties = (
        f"ALTER TABLE {target} SET TBLPROPERTIES ("
        f"'delta.columnMapping.mode' = 'name', "
        f"'delta.universalFormat.enabledFormats' = 'iceberg')"
    )
    optimize_cmd = f"OPTIMIZE {target}"

    logger.info("Enabling Delta UniForm Iceberg metadata generation on '%s'...", target)
    try:
        spark.sql(ddl_properties)
        spark.sql(optimize_cmd)
        logger.info("✔ Delta UniForm successfully activated on '%s'.", target)
        return {
            "status": "SUCCESS",
            "table": table_name,
            "universal_formats": ["iceberg"],
            "column_mapping": "name",
        }
    except Exception as exc:
        logger.error("Failed to enable UniForm on '%s': %s", table_name, exc)
        return {"status": "ERROR", "table": table_name, "error": str(exc)}


def read_iceberg_table(
    spark: SparkSession,
    table_or_path: str,
    as_of_snapshot_id: Optional[int] = None,
    as_of_timestamp: Optional[str] = None,
) -> DataFrame:
    """Reads an Apache Iceberg table with optional snapshot or timestamp time-travel.
    
    Args:
        spark: Active SparkSession.
        table_or_path: Iceberg catalog table identifier or warehouse path.
        as_of_snapshot_id: Target snapshot ID for point-in-time time travel.
        as_of_timestamp: Target ISO-8601 or Spark-compatible timestamp string.
        
    Returns:
        Loaded Iceberg DataFrame.
    """
    reader = spark.read.format("iceberg")

    if as_of_snapshot_id is not None:
        reader = reader.option("as-of-snapshot-id", str(as_of_snapshot_id))
    elif as_of_timestamp is not None:
        reader = reader.option("as-of-timestamp-millis", str(as_of_timestamp))

    logger.info("Loading Iceberg table '%s'...", table_or_path)
    return reader.load(table_or_path)


def write_iceberg_table(
    df: DataFrame,
    table_name: str,
    mode: str = "append",
    partition_by: Optional[List[str]] = None,
) -> None:
    """Writes a DataFrame to an Apache Iceberg table.
    
    Args:
        df: Input DataFrame to save.
        table_name: Target Iceberg table name.
        mode: Save mode ('append' or 'overwrite').
        partition_by: Optional partition column list.
    """
    writer = df.write.format("iceberg").mode(mode)
    if partition_by:
        writer = writer.partitionBy(*partition_by)

    logger.info("Saving records to Iceberg table '%s' (mode=%s)...", table_name, mode)
    writer.saveAsTable(table_name)


def inspect_iceberg_metadata(spark: SparkSession, table_name: str) -> Dict[str, Any]:
    """Queries Iceberg table snapshots and metadata history."""
    try:
        snapshots_df = spark.sql(
            f"SELECT snapshot_id, committed_at, operation FROM {table_name}.snapshots ORDER BY committed_at DESC LIMIT 10"
        )
        snapshots = [row.asDict() for row in snapshots_df.collect()]
        return {
            "status": "SUCCESS",
            "table": table_name,
            "recent_snapshots": snapshots,
        }
    except Exception as exc:
        return {
            "status": "ERROR",
            "table": table_name,
            "error": str(exc),
        }
