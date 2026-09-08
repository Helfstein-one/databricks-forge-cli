"""Structured Logging and Observability Module for Data Pipelines.

Provides JSON formatted logs, pipeline audit decorators with latency tracking,
and persistence to a Delta Lake audit table (`pipeline_execution_audit`).
"""

from __future__ import annotations

import datetime
import functools
import json
import logging
import os
import sys
import time
from typing import Any, Callable, Dict, Optional

try:
    from pyspark.sql import DataFrame, SparkSession
except ImportError:
    class DataFrame:  # type: ignore
        pass

    class SparkSession:  # type: ignore
        pass

logger = logging.getLogger(__name__)


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects for log aggregators (Datadog, CloudWatch, etc.)."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.datetime.fromtimestamp(record.created, datetime.timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include custom extra fields if provided
        for key, val in record.__dict__.items():
            if key not in (
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "id", "levelname", "levelno", "lineno", "module",
                "msecs", "message", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread", "threadName"
            ):
                log_entry[key] = val

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def setup_pipeline_logging(
    level: str = "INFO",
    json_format: bool = True,
    logger_name: Optional[str] = None,
) -> logging.Logger:
    """Configures structured logging for data pipeline execution.
    
    Args:
        level: Logging severity string (e.g. 'DEBUG', 'INFO', 'WARNING').
        json_format: If True, formats output as JSON strings.
        logger_name: Specific logger name or None for root logger.
        
    Returns:
        Configured Logger instance.
    """
    target_logger = logging.getLogger(logger_name)
    target_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers to avoid duplicates
    if target_logger.hasHandlers():
        target_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if json_format:
        handler.setFormatter(StructuredJsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s - %(message)s")
        )

    target_logger.addHandler(handler)
    target_logger.propagate = False
    return target_logger


def record_audit_log(
    spark: SparkSession,
    audit_record: Dict[str, Any],
    audit_table: str = "pipeline_execution_audit",
) -> None:
    """Persists an execution audit record into a Delta Lake audit table.
    
    Args:
        spark: Active SparkSession.
        audit_record: Dictionary containing audit telemetry fields.
        audit_table: Target audit table name.
    """
    try:
        df = spark.createDataFrame([audit_record])
        df.write.format("delta").mode("append").saveAsTable(audit_table)
        logger.debug("Persisted audit event to Delta table '%s'", audit_table)
    except Exception as exc:
        logger.warning("Could not persist audit record to '%s': %s", audit_table, exc)


def pipeline_audit_step(step_name: Optional[str] = None):
    """Decorator for auditing pipeline step execution.
    
    Measures duration, records row count when a DataFrame is returned, logs start/completion,
    and captures failures with duration tracking.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = step_name or func.__name__
            start_time = time.perf_counter()
            started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            logger.info("Starting pipeline step: %s", name, extra={"step": name, "status": "STARTED"})

            try:
                result = func(*args, **kwargs)
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                row_count = None

                if isinstance(result, DataFrame):
                    try:
                        row_count = result.count()
                    except Exception:
                        row_count = None

                extra_payload: Dict[str, Any] = {
                    "step": name,
                    "status": "COMPLETED",
                    "duration_ms": elapsed_ms,
                    "started_at": started_at,
                }
                if row_count is not None:
                    extra_payload["row_count"] = row_count

                logger.info(
                    "Completed pipeline step '%s' in %.2f ms (rows: %s)",
                    name,
                    elapsed_ms,
                    row_count if row_count is not None else "N/A",
                    extra=extra_payload,
                )
                return result

            except Exception as exc:
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                logger.error(
                    "Failed pipeline step '%s' after %.2f ms: %s",
                    name,
                    elapsed_ms,
                    exc,
                    extra={
                        "step": name,
                        "status": "FAILED",
                        "duration_ms": elapsed_ms,
                        "error": str(exc),
                        "started_at": started_at,
                    },
                    exc_info=True,
                )
                raise

        return wrapper
    return decorator
