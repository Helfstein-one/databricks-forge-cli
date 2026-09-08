"""Core file format conversion and inspection engine for Lakehouse data pipelines."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

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


def detect_format_from_path(path: str | Path) -> str:
    """Infers the data file format from a file path or URI.
    
    Args:
        path: File or directory path string.
        
    Returns:
        Canonical format identifier (e.g. 'parquet', 'delta', 'csv').
    """
    path_str = str(path).lower().rstrip("/")
    if (
        path_str.endswith(".delta")
        or "/_delta_log" in path_str
        or path_str.startswith("delta.`")
    ):
        return "delta"
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

    # Default fallback to delta for lakehouse directories without extensions
    return "delta"


def build_convert_plan(
    source: str,
    target: str,
    from_format: Optional[str] = None,
    to_format: Optional[str] = None,
    partition_by: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Builds a structured execution plan for converting datasets across formats.
    
    Args:
        source: Source file path or table name.
        target: Destination file path or table name.
        from_format: Explicit source format (or auto-detected if None).
        to_format: Explicit target format (defaults to 'delta' if None).
        partition_by: Optional partitioning column names.
        
    Returns:
        Structured conversion plan dictionary.
    """
    src_fmt = from_format.lower() if from_format else detect_format_from_path(source)
    tgt_fmt = to_format.lower() if to_format else "delta"

    if src_fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported source format '{src_fmt}'. Supported: {', '.join(SUPPORTED_FORMATS)}"
        )
    if tgt_fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported target format '{tgt_fmt}'. Supported: {', '.join(SUPPORTED_FORMATS)}"
        )

    read_opts = DEFAULT_READ_OPTIONS.get(src_fmt, {}).copy()

    plan = {
        "status": "PLANNED",
        "source": source,
        "target": target,
        "source_format": src_fmt,
        "target_format": tgt_fmt,
        "read_options": read_opts,
        "partition_by": partition_by or [],
        "command_preview": (
            f"spark.read.format('{src_fmt}').load('{source}')"
            f".write.format('{tgt_fmt}')"
            + (f".partitionBy({partition_by})" if partition_by else "")
            + f".save('{target}')"
        ),
    }
    return plan
