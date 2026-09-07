"""Integration tests verifying CatalogManager persistence with local Delta Lake storage."""

import pytest
from {{project_slug}}.catalog import CatalogManager
from {{project_slug}}.pipelines.example_pipeline import generate_synthetic_bronze_data


def test_catalog_manager_save_and_load(spark_session, temp_lakehouse_dir):
    """Verifies that CatalogManager writes Delta tables to disk and reads them accurately."""
    catalog = CatalogManager(spark=spark_session, storage_root=temp_lakehouse_dir)

    # 1. Generate test DataFrame
    bronze_df = generate_synthetic_bronze_data(spark_session, row_count=25)
    
    # 2. Save table
    catalog.save_table(bronze_df, "test_bronze_table", mode="overwrite")

    # 3. Check table exists
    assert catalog.table_exists("test_bronze_table") is True

    # 4. Load table and assert counts
    loaded_df = catalog.load_table("test_bronze_table")
    assert loaded_df.count() == 25
    assert "transaction_id" in loaded_df.columns
    assert "user_id" in loaded_df.columns


def test_catalog_manager_partitioning(spark_session, temp_lakehouse_dir):
    """Verifies that partition_by properly segments Delta Lake files."""
    catalog = CatalogManager(spark=spark_session, storage_root=temp_lakehouse_dir)
    data = [
        ("ID_1", "US", 10.0),
        ("ID_2", "US", 20.0),
        ("ID_3", "EU", 30.0),
    ]
    df = spark_session.createDataFrame(data, ["id", "region", "val"])

    catalog.save_table(df, "partitioned_table", mode="overwrite", partition_by=["region"])

    loaded = catalog.load_table("partitioned_table")
    assert loaded.count() == 3

    # Check partition directories exist on disk
    table_path = catalog.get_local_path("partitioned_table")
    assert (table_path / "region=US").exists()
    assert (table_path / "region=EU").exists()
