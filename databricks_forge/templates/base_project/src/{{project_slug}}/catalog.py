"""Catalog abstraction layer separating local Delta storage from Databricks Metastore."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional
from pyspark.sql import DataFrame, SparkSession

logger = logging.getLogger(__name__)


class CatalogManager:
    """Provides a unified API for reading and writing Delta tables across environments.
    
    In 'local' mode: Persists Delta tables as directory structures inside LOCAL_STORAGE_PATH.
    In 'remote' / Databricks mode: Interacts with Databricks Metastore or Unity Catalog tables.
    """

    def __init__(self, spark: SparkSession, storage_root: Optional[str] = None):
        self.spark = spark
        self.mode = os.getenv("EXECUTION_MODE", "local").strip().lower()
        self.storage_root = Path(storage_root or os.getenv("LOCAL_STORAGE_PATH", "./data_lake")).resolve()

    def get_local_path(self, table_name: str) -> Path:
        """Translates a database.table or schema.table notation into local directory path."""
        sanitized = table_name.replace(".", "/")
        return self.storage_root / sanitized

    def load_table(self, table_name: str) -> DataFrame:
        """Loads a Delta table from metastore (remote) or disk (local)."""
        if self.mode in ("remote", "databricks", "connect"):
            logger.info("Loading table '%s' from Databricks Catalog.", table_name)
            return self.spark.read.table(table_name)

        target_path = self.get_local_path(table_name)
        logger.info("Loading local Delta table from path: %s", target_path)
        return self.spark.read.format("delta").load(str(target_path))

    def save_table(
        self,
        df: DataFrame,
        table_name: str,
        mode: str = "overwrite",
        partition_by: Optional[list[str]] = None
    ) -> None:
        """Saves a DataFrame as a Delta table."""
        if self.mode in ("remote", "databricks", "connect"):
            logger.info("Saving table '%s' to Databricks Catalog (mode=%s).", table_name, mode)
            writer = df.write.format("delta").mode(mode)
            if partition_by:
                writer = writer.partitionBy(*partition_by)
            writer.saveAsTable(table_name)
            return

        target_path = self.get_local_path(table_name)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Saving local Delta table to path: %s (mode=%s).", target_path, mode)
        writer = df.write.format("delta").mode(mode)
        if partition_by:
            writer = writer.partitionBy(*partition_by)
        writer.save(str(target_path))

    def table_exists(self, table_name: str) -> bool:
        """Checks whether the table exists in catalog or on filesystem."""
        if self.mode in ("remote", "databricks", "connect"):
            return self.spark.catalog.tableExists(table_name)

        target_path = self.get_local_path(table_name)
        return target_path.exists() and (target_path / "_delta_log").exists()
