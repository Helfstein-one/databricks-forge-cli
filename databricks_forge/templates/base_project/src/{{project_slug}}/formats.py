"""Multi-Format Data I/O and Conversion Module for {{project_name}} Lakehouse.

Supports seamless ingestion, transformation, and export across:
- Parquet (.parquet)
- ORC (.orc)
- Avro (.avro)
- CSV (.csv)
- JSON / JSONL (.json, .jsonl)
- Delta Lake (.delta)
- Apache Iceberg (.iceberg)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from pyspark.sql import DataFrame, SparkSession
except ImportError:
    class DataFrame:  # type: ignore
        pass

    class SparkSession:  # type: ignore
        pass

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = [
    "parquet",
    "orc",
    "avro",
    "csv",
    "json",
    "jsonl",
    "delta",
    "iceberg",
]

DEFAULT_READ_OPTIONS: Dict[str, Dict[str, str]] = {
    "csv": {
        "header": "true",
        "inferSchema": "true",
        "mode": "PERMISSIVE",
    },
    "json": {
        "multiLine": "false",
        "mode": "PERMISSIVE",
    },
    "jsonl": {
        "multiLine": "false",
        "mode": "PERMISSIVE",
    },
    "parquet": {},
    "orc": {},
    "avro": {},
    "delta": {},
    "iceberg": {},
}


def detect_format(path: str | Path) -> str:
    """Infers the data file format from a file path or URI."""
    path_str = str(path).lower().rstrip("/")
    if path_str.endswith(".parquet") or ".parquet." in path_str:
        return "parquet"
    if path_str.endswith(".orc"):
        return "orc"
    if path_str.endswith(".avro"):
        return "avro"
    if path_str.endswith(".csv") or path_str.endswith(".tsv"):
        return "csv"
    if path_str.endswith(".json") or path_str.endswith(".jsonl"):
        return "json"
    if "iceberg" in path_str or "/metadata" in path_str:
        return "iceberg"
    return "delta"


def read_dataset(
    spark: SparkSession,
    path_or_table: str,
    format: str = "auto",
    options: Optional[Dict[str, str]] = None,
) -> DataFrame:
    """Reads a dataset from any supported format into a PySpark DataFrame.
    
    Args:
        spark: Active SparkSession.
        path_or_table: Source file path, directory, or metastore table name.
        format: Format identifier or 'auto' to infer from extension.
        options: Optional format-specific read options (e.g. delimiter, header).
        
    Returns:
        Loaded PySpark DataFrame.
    """
    resolved_format = (
        detect_format(path_or_table) if format.lower() == "auto" else format.lower()
    )
    if resolved_format not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format '{resolved_format}'. Supported: {', '.join(SUPPORTED_FORMATS)}"
        )

    read_opts = DEFAULT_READ_OPTIONS.get(resolved_format, {}).copy()
    if options:
        read_opts.update(options)

    logger.info("Reading dataset from '%s' using format '%s'...", path_or_table, resolved_format)

    # If it's a catalog table reference without file extensions
    if (
        not any(path_or_table.endswith(f".{ext}") for ext in ("parquet", "orc", "avro", "csv", "json", "delta"))
        and "/" not in path_or_table
        and "\\" not in path_or_table
    ):
        return spark.read.format(resolved_format).table(path_or_table)

    reader = spark.read.format(resolved_format).options(**read_opts)
    return reader.load(path_or_table)


def write_dataset(
    df: DataFrame,
    path_or_table: str,
    format: str = "delta",
    mode: str = "overwrite",
    partition_by: Optional[List[str]] = None,
    options: Optional[Dict[str, str]] = None,
) -> None:
    """Writes a DataFrame to storage or catalog in the requested format.
    
    Args:
        df: Input DataFrame to persist.
        path_or_table: Destination path or catalog table name.
        format: Target format ('delta', 'parquet', 'orc', 'avro', 'csv', 'json', 'iceberg').
        mode: Save mode ('overwrite', 'append', 'ignore', 'errorifexists').
        partition_by: Optional column names for partitioning.
        options: Optional format-specific write options.
    """
    fmt = format.lower()
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported target format '{fmt}'. Supported: {', '.join(SUPPORTED_FORMATS)}")

    logger.info("Persisting dataset to '%s' (format=%s, mode=%s)...", path_or_table, fmt, mode)

    writer = df.write.format(fmt).mode(mode)
    if partition_by:
        writer = writer.partitionBy(*partition_by)
    if options:
        writer = writer.options(**options)

    is_table = (
        not any(path_or_table.endswith(f".{ext}") for ext in ("parquet", "orc", "avro", "csv", "json", "delta"))
        and "/" not in path_or_table
        and "\\" not in path_or_table
    )

    if is_table:
        writer.saveAsTable(path_or_table)
    else:
        writer.save(path_or_table)


def convert_dataset(
    spark: SparkSession,
    source_path: str,
    target_path: str,
    from_format: str = "auto",
    to_format: str = "delta",
    partition_by: Optional[List[str]] = None,
    options: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Converts a dataset directly between file formats with optional partitioning."""
    df = read_dataset(spark, source_path, format=from_format, options=options)
    write_dataset(df, target_path, format=to_format, partition_by=partition_by)

    return {
        "status": "SUCCESS",
        "source": source_path,
        "target": target_path,
        "from_format": from_format,
        "to_format": to_format,
        "row_count": df.count(),
    }
