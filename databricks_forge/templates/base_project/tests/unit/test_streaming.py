"""Unit tests for Structured Streaming transformations."""

import pytest
from pyspark.sql.types import (
    DoubleType,
    StringType,
    StructField,
    StructType,
)
from {{project_slug}}.pipelines.streaming_pipeline import (
    transform_streaming_transactions,
    aggregate_streaming_windows,
)


def test_transform_streaming_transactions_cleans_stream(spark_session, sample_transactions_schema):
    """Verifies that transform_streaming_transactions correctly filters invalid records and standardizes fields."""
    input_data = [
        ("TX_S1", "USER_A", 120.0, "completed", "tech", "2026-03-01 10:00:00"),
        ("TX_S2", "USER_B", -15.0, "COMPLETED", "food", "2026-03-01 10:01:00"),  # negative amount filtered
        ("TX_S3", "USER_C", 50.0, "INVALID", "home", "2026-03-01 10:02:00"),      # invalid status filtered
        ("TX_S4", "USER_D", 85.5, " PENDING ", "tech", "2026-03-01 10:03:00"),    # valid trimmed pending
    ]
    raw_df = spark_session.createDataFrame(input_data, schema=sample_transactions_schema)

    cleaned_df = transform_streaming_transactions(raw_df, watermark_delay="5 minutes")

    assert cleaned_df.count() == 2
    row_ids = [r["transaction_id"] for r in cleaned_df.select("transaction_id").collect()]
    assert set(row_ids) == {"TX_S1", "TX_S4"}

    statuses = [r["status"] for r in cleaned_df.select("status").collect()]
    assert set(statuses) == {"COMPLETED", "PENDING"}


def test_aggregate_streaming_windows_groups_by_window(spark_session, sample_transactions_schema):
    """Verifies that aggregate_streaming_windows calculates windowed aggregations over completed transactions."""
    input_data = [
        ("TX_W1", "USER_A", 100.0, "COMPLETED", "tech", "2026-03-01 10:01:00"),
        ("TX_W2", "USER_B", 200.0, "COMPLETED", "tech", "2026-03-01 10:02:00"),
        ("TX_W3", "USER_C", 50.0, "PENDING", "tech", "2026-03-01 10:03:00"),     # Pending excluded
        ("TX_W4", "USER_D", 300.0, "COMPLETED", "food", "2026-03-01 10:04:00"),   # Different category
    ]
    raw_df = spark_session.createDataFrame(input_data, schema=sample_transactions_schema)
    cleaned_df = transform_streaming_transactions(raw_df, watermark_delay="5 minutes")

    windows_df = aggregate_streaming_windows(cleaned_df, window_duration="5 minutes")

    rows = windows_df.collect()
    assert len(rows) == 2  # tech and food windows

    tech_row = next(r for r in rows if r["category"] == "tech")
    assert tech_row["window_total_spend"] == 300.0
    assert tech_row["window_tx_count"] == 2
    assert tech_row["window_avg_spend"] == 150.0

    food_row = next(r for r in rows if r["category"] == "food")
    assert food_row["window_total_spend"] == 300.0
    assert food_row["window_tx_count"] == 1
