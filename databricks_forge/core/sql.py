"""SQL Job execution and deployment module for Databricks Lakehouse."""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from databricks_forge.core.client import DatabricksCEClient, DatabricksClientError

logger = logging.getLogger(__name__)


class SQLJobError(Exception):
    """Raised when a SQL job fails."""
    pass


def split_sql_statements(sql_content: str) -> List[str]:
    """Splits raw SQL file contents into individual executable statements.
    
    Ignores SQL comments (-- and /* */) and trims empty statements.
    """
    # Remove single-line comments
    cleaned = re.sub(r"--.*$", "", sql_content, flags=re.MULTILINE)
    # Remove multi-line comments
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)

    statements = [stmt.strip() for stmt in cleaned.split(";") if stmt.strip()]
    return statements


def execute_sql_locally(
    sql_file: Path | str,
    spark_session: Optional[Any] = None,
    mode: str = "local"
) -> List[Dict[str, Any]]:
    """Executes a SQL file locally or via Databricks Connect using SparkSession.
    
    Args:
        sql_file: Path to .sql file.
        spark_session: Optional pre-existing SparkSession.
        mode: 'local' or 'remote' (for Databricks Connect).
        
    Returns:
        List of results containing executed statement, execution time, and row count if applicable.
    """
    path = Path(sql_file).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"SQL file not found: {path}")

    sql_text = path.read_text(encoding="utf-8")
    statements = split_sql_statements(sql_text)

    if not statements:
        logger.warning("No executable statements found in %s", path)
        return []

    # If no session provided, initialize using standard PySpark session factory
    if spark_session is None:
        try:
            from pyspark.sql import SparkSession
            spark_session = (
                SparkSession.builder
                .appName(f"ForgeSQLJob-{path.stem}")
                .master("local[*]")
                .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
                .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
                .getOrCreate()
            )
        except Exception as exc:
            raise SQLJobError(f"Failed to initialize local Spark engine to run SQL: {exc}") from exc

    results: List[Dict[str, Any]] = []

    for idx, stmt in enumerate(statements, start=1):
        start_t = time.perf_counter()
        try:
            df = spark_session.sql(stmt)
            count = None
            # Only count rows if it produces a result set (SELECT, SHOW, DESCRIBE)
            first_word = stmt.strip().split()[0].upper()
            if first_word in ("SELECT", "WITH", "SHOW", "DESCRIBE", "EXPLAIN"):
                count = df.count()

            duration = time.perf_counter() - start_t
            results.append({
                "statement_index": idx,
                "statement_preview": stmt[:80].replace("\n", " ") + ("..." if len(stmt) > 80 else ""),
                "status": "SUCCESS",
                "row_count": count,
                "duration_seconds": round(duration, 3),
            })
        except Exception as exc:
            duration = time.perf_counter() - start_t
            results.append({
                "statement_index": idx,
                "statement_preview": stmt[:80].replace("\n", " "),
                "status": "FAILED",
                "error": str(exc),
                "duration_seconds": round(duration, 3),
            })
            raise SQLJobError(f"SQL statement #{idx} failed: {exc}\nStatement:\n{stmt}") from exc

    return results


def deploy_sql_to_workspace(
    sql_file: Path | str,
    client: DatabricksCEClient,
    remote_workspace_path: str,
    overwrite: bool = True
) -> Dict[str, Any]:
    """Deploys a SQL script to Databricks Workspace as a native SQL Source file."""
    path = Path(sql_file).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"SQL file not found: {path}")

    # Remove trailing .sql from remote path if present to follow Databricks workspace object naming
    clean_remote = remote_workspace_path
    if clean_remote.endswith(".sql"):
        clean_remote = clean_remote[:-4]

    return client.upload_file(
        local_path=path,
        remote_workspace_path=clean_remote,
        file_format="SOURCE",
        language="SQL",
        overwrite=overwrite,
    )
