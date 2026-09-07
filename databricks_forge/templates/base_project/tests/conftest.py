"""Pytest configuration and shared fixtures for PySpark and Chispa testing."""

import os
import shutil
import tempfile
import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import DoubleType, StringType, StructField, StructType


@pytest.fixture(scope="session")
def spark_session():
    """Provides a local SparkSession with Delta Lake support for tests."""
    builder = (
        SparkSession.builder
        .appName("{{project_name}}-Tests")
        .master("local[2]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.ui.enabled", "false")
        .config("spark.driver.bindAddress", "127.0.0.1")
    )
    spark = builder.getOrCreate()
    yield spark
    spark.stop()


@pytest.fixture
def temp_lakehouse_dir():
    """Creates a temporary directory for Delta Lake storage during tests."""
    tmp = tempfile.mkdtemp(prefix="forge_test_lake_")
    os.environ["LOCAL_STORAGE_PATH"] = tmp
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def sample_transactions_schema():
    """Returns the transactions schema for tests."""
    return StructType([
        StructField("transaction_id", StringType(), False),
        StructField("user_id", StringType(), False),
        StructField("amount", DoubleType(), True),
        StructField("status", StringType(), True),
        StructField("category", StringType(), True),
        StructField("created_at", StringType(), True),
    ])
