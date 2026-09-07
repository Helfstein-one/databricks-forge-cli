"""SparkSession Factory with Dual-Runtime Support (Local Delta vs Databricks Connect)."""

from __future__ import annotations

import logging
import os
from typing import Optional
from pyspark.sql import SparkSession

logger = logging.getLogger(__name__)


def get_spark(mode: Optional[str] = None, app_name: Optional[str] = None) -> SparkSession:
    """Returns an active SparkSession configured for local execution or remote Databricks Connect.
    
    Args:
        mode: 'local' or 'remote'. Defaults to EXECUTION_MODE env var or 'local'.
        app_name: Name of the Spark Application.

    Returns:
        Configured SparkSession or DatabricksSession instance.
    """
    exec_mode = (mode or os.getenv("EXECUTION_MODE", "local")).strip().lower()
    app = app_name or "{{project_name}}-Pipeline"

    if exec_mode in ("remote", "databricks", "connect"):
        host = os.getenv("DATABRICKS_HOST")
        token = os.getenv("DATABRICKS_TOKEN")
        cluster_id = os.getenv("DATABRICKS_CLUSTER_ID")

        if not host or not token:
            raise ValueError(
                "Remote execution requires DATABRICKS_HOST and DATABRICKS_TOKEN environment variables."
            )

        try:
            from databricks.connect import DatabricksSession
            builder = DatabricksSession.builder.remote(
                host=host,
                token=token,
                cluster_id=cluster_id
            )
            logger.info("Initializing DatabricksSession via Databricks Connect v2 (%s)", host)
            return builder.getOrCreate()
        except ImportError as exc:
            raise ImportError(
                "databricks-connect is required for remote execution. Run 'pip install databricks-connect'."
            ) from exc

    # Local Execution (Local PySpark + Delta Lake)
    logger.info("Initializing local PySpark session with Delta Lake support.")
    builder = (
        SparkSession.builder
        .appName(app)
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.driver.memory", os.getenv("SPARK_DRIVER_MEMORY", "4g"))
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.ui.enabled", "false")
    )

    return builder.getOrCreate()
