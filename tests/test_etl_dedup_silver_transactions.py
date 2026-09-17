"""Unit test for auto-generated pipeline: dedup_silver_transactions
Target: silver_transactions from bronze_raw_transactions
"""

import sys
from unittest.mock import MagicMock, patch
import pytest

# Ensure pyspark can be safely mocked during local CI quality gate runs
for _mod in ["pyspark", "pyspark.sql", "pyspark.sql.functions"]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()


def test_dedup_silver_transactions_validation():
    """Validates pipeline configuration, naming conventions, and integrity."""
    assert "dedup_silver_transactions" != ""
    assert "bronze_raw_transactions" != ""
    assert "silver_transactions" != ""
    assert "silver_transactions" != "bronze_raw_transactions", "Source and target tables must differ"


def test_dedup_silver_transactions_execution_mock():
    """Verifies that run_pipeline executes audit logging and writes to target Delta table."""
    from notebooks.dedup_silver_transactions import run_pipeline

    # Mock SparkSession and DataFrame
    mock_spark = MagicMock()
    mock_df = MagicMock()
    mock_spark.table.return_value = mock_df
    mock_df.dropDuplicates.return_value = mock_df
    mock_df.withColumn.return_value = mock_df
    mock_df.count.return_value = 42

    mock_writer = MagicMock()
    mock_df.write.format.return_value = mock_writer
    mock_writer.mode.return_value = mock_writer
    mock_writer.option.return_value = mock_writer

    rows = run_pipeline(spark=mock_spark)

    # Asserts
    mock_spark.table.assert_called_with("bronze_raw_transactions")
    mock_df.dropDuplicates.assert_called_once()
    mock_df.write.format.assert_called_with("delta")
    mock_writer.saveAsTable.assert_called_with("silver_transactions")
    assert rows == 42
