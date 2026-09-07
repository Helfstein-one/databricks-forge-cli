"""Unit tests for pipeline transformations using Chispa for DataFrame assertions."""

import pytest
from datetime import date
from pyspark.sql.types import (
    BooleanType,
    DateType,
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
)
from {{project_slug}}.pipelines.example_pipeline import (
    clean_transactions,
    aggregate_daily_metrics,
)

try:
    from chispa.dataframe_comparer import assert_df_equality
except ImportError:
    # Graceful fallback assertion if chispa is missing
    def assert_df_equality(df1, df2, ignore_row_order=False, ignore_column_order=False, **kwargs):
        c1 = [tuple(r.asDict().values()) for r in df1.collect()]
        c2 = [tuple(r.asDict().values()) for r in df2.collect()]
        if ignore_row_order:
            c1.sort()
            c2.sort()
        assert c1 == c2


def test_clean_transactions_filters_and_transforms(spark_session, sample_transactions_schema):
    """Verifies that clean_transactions filters invalid amounts/statuses and adds parsed date."""
    input_data = [
        ("TX_001", "U_100", 150.0, " completed ", "tech", "2026-03-01 10:00:00"),
        ("TX_002", "U_100", -50.0, "COMPLETED", "tech", "2026-03-01 11:00:00"),      # invalid negative
        ("TX_003", "U_200", 25.5, "UNKNOWN_STATUS", "food", "2026-03-01 12:00:00"),  # invalid status
        ("TX_004", "U_200", 80.0, "PENDING", "fashion", "2026-03-01 13:00:00"),       # valid pending
    ]
    raw_df = spark_session.createDataFrame(input_data, schema=sample_transactions_schema)

    cleaned_df = clean_transactions(raw_df)

    # Validate row count
    assert cleaned_df.count() == 2

    # Validate contents of remaining valid rows
    user_ids = [r["user_id"] for r in cleaned_df.select("user_id").collect()]
    assert set(user_ids) == {"U_100", "U_200"}

    # Validate status normalization
    statuses = [r["status"] for r in cleaned_df.select("status").collect()]
    assert set(statuses) == {"COMPLETED", "PENDING"}


def test_aggregate_daily_metrics(spark_session):
    """Verifies Gold layer aggregation logic, high-value user flags, and schema."""
    input_schema = StructType([
        StructField("user_id", StringType(), False),
        StructField("status", StringType(), True),
        StructField("amount", DoubleType(), True),
        StructField("date", DateType(), True),
    ])
    input_data = [
        ("U_1", "COMPLETED", 600.0, date(2026, 3, 1)),
        ("U_1", "COMPLETED", 500.0, date(2026, 3, 1)),  # Sum = 1100 -> High Value = True
        ("U_2", "COMPLETED", 200.0, date(2026, 3, 1)),  # Sum = 200  -> High Value = False
        ("U_2", "PENDING", 999.0, date(2026, 3, 1)),    # Ignored (not completed)
    ]
    df = spark_session.createDataFrame(input_data, schema=input_schema)

    metrics_df = aggregate_daily_metrics(df)

    expected_schema = StructType([
        StructField("user_id", StringType(), False),
        StructField("date", DateType(), True),
        StructField("total_spend", DoubleType(), True),
        StructField("transaction_count", LongType(), False),
        StructField("avg_transaction_amount", DoubleType(), True),
        StructField("is_high_value", BooleanType(), True),
    ])
    expected_data = [
        ("U_1", date(2026, 3, 1), 1100.0, 2, 550.0, True),
        ("U_2", date(2026, 3, 1), 200.0, 1, 200.0, False),
    ]
    expected_df = spark_session.createDataFrame(expected_data, schema=expected_schema)

    assert_df_equality(metrics_df, expected_df, ignore_row_order=True)
