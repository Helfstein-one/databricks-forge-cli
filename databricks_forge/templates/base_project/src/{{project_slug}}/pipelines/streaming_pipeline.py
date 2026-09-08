"""Structured Streaming Pipeline with Delta Lake and Watermarking."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

try:
    from pyspark.sql import DataFrame, SparkSession
    from pyspark.sql import functions as F
    from pyspark.sql.streaming import StreamingQuery
except ImportError:
    DataFrame = Any  # type: ignore
    SparkSession = Any  # type: ignore
    StreamingQuery = Any  # type: ignore
    F = Any  # type: ignore

logger = logging.getLogger(__name__)


def transform_streaming_transactions(stream_df: DataFrame, watermark_delay: str = "10 minutes") -> DataFrame:
    """Applies streaming cleansing and windowed aggregations with watermarking.
    
    Operations:
    - Parses string timestamp to TimestampType
    - Applies watermark to handle late-arriving data
    - Filters invalid or non-positive amounts
    - Normalizes status values to uppercase
    """
    valid_statuses = ["COMPLETED", "PENDING", "REFUNDED"]

    cleaned = (
        stream_df
        .filter(F.col("transaction_id").isNotNull() & F.col("user_id").isNotNull())
        .withColumn("status", F.upper(F.trim(F.col("status"))))
        .filter(F.col("status").isin(valid_statuses))
        .filter(F.col("amount").isNotNull() & (F.col("amount") > 0.0))
        .withColumn("timestamp", F.to_timestamp(F.col("created_at")))
        .withColumn("date", F.to_date(F.col("timestamp")))
        .withWatermark("timestamp", watermark_delay)
    )
    return cleaned


def aggregate_streaming_windows(stream_df: DataFrame, window_duration: str = "5 minutes") -> DataFrame:
    """Calculates tumbling window metrics over streaming transactions."""
    return (
        stream_df
        .filter(F.col("status") == "COMPLETED")
        .groupBy(
            F.window(F.col("timestamp"), window_duration),
            F.col("category")
        )
        .agg(
            F.round(F.sum("amount"), 2).alias("window_total_spend"),
            F.count("transaction_id").alias("window_tx_count"),
            F.round(F.avg("amount"), 2).alias("window_avg_spend"),
        )
        .select(
            F.col("window.start").alias("window_start"),
            F.col("window.end").alias("window_end"),
            F.col("category"),
            F.col("window_total_spend"),
            F.col("window_tx_count"),
            F.col("window_avg_spend"),
        )
    )


def start_streaming_pipeline(
    spark: SparkSession,
    source_table: str,
    target_table: str,
    checkpoint_path: str,
    trigger_available_now: bool = True,
    processing_time: Optional[str] = None,
) -> StreamingQuery:
    """Starts the Delta Lake Structured Streaming query.
    
    Args:
        spark: Active SparkSession.
        source_table: Input Delta table name or path.
        target_table: Output Delta table name or path.
        checkpoint_path: Checkpoint directory location for fault-tolerance.
        trigger_available_now: If True, processes all available data like a micro-batch (AvailableNow).
        processing_time: Micro-batch trigger interval (e.g. '10 seconds').
        
    Returns:
        Active StreamingQuery handle.
    """
    logger.info("Initializing Structured Streaming query from '%s' to '%s'...", source_table, target_table)

    # Read stream from Delta source
    source_stream = spark.readStream.format("delta").table(source_table)
    transformed_stream = transform_streaming_transactions(source_stream)

    writer = (
        transformed_stream
        .writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", checkpoint_path)
    )

    if trigger_available_now:
        # Cost-effective micro-batch trigger for Databricks CE and scheduled jobs
        writer = writer.trigger(availableNow=True)
    elif processing_time:
        writer = writer.trigger(processingTime=processing_time)

    query = writer.toTable(target_table)
    logger.info("Streaming query started with Query ID: %s", query.id)
    return query
