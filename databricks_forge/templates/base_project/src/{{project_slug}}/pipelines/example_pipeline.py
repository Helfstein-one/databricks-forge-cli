"""Example Medallion Lakehouse Pipeline (Bronze -> Silver -> Gold)."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, IntegerType, StringType, StructField, StructType, TimestampType

logger = logging.getLogger(__name__)


def get_raw_transactions_schema() -> StructType:
    """Schema definition for incoming raw bronze transactions."""
    return StructType([
        StructField("transaction_id", StringType(), False),
        StructField("user_id", StringType(), False),
        StructField("amount", DoubleType(), True),
        StructField("status", StringType(), True),
        StructField("category", StringType(), True),
        StructField("created_at", StringType(), True),
    ])


def clean_transactions(df: DataFrame) -> DataFrame:
    """Silver layer transformation: cleans and standardizes raw transactions.
    
    Operations:
    - Trims strings and forces uppercase status
    - Filters out null or negative amounts
    - Filters invalid status values
    - Parses ISO timestamp string into TimestampType
    - Appends ingestion audit metadata
    """
    valid_statuses = ["COMPLETED", "PENDING", "REFUNDED"]

    return (
        df
        .filter(F.col("transaction_id").isNotNull() & F.col("user_id").isNotNull())
        .withColumn("status", F.upper(F.trim(F.col("status"))))
        .filter(F.col("status").isin(valid_statuses))
        .filter(F.col("amount").isNotNull() & (F.col("amount") > 0.0))
        .withColumn("timestamp", F.to_timestamp(F.col("created_at")))
        .withColumn("date", F.to_date(F.col("timestamp")))
        .withColumn("_ingested_at", F.current_timestamp())
    )


def aggregate_daily_metrics(df: DataFrame) -> DataFrame:
    """Gold layer aggregation: calculates daily customer metrics.
    
    Aggregations:
    - Total spend per user per date
    - Total transaction count
    - Average transaction amount
    - High-value user flag (spend > 1000)
    """
    return (
        df
        .filter(F.col("status") == "COMPLETED")
        .groupBy("user_id", "date")
        .agg(
            F.round(F.sum("amount"), 2).alias("total_spend"),
            F.count("transaction_id").alias("transaction_count"),
            F.round(F.avg("amount"), 2).alias("avg_transaction_amount"),
        )
        .withColumn("is_high_value", F.col("total_spend") >= 1000.0)
        .sort("user_id", "date")
    )


def generate_synthetic_bronze_data(spark: SparkSession, row_count: int = 100) -> DataFrame:
    """Generates synthetic bronze data for testing or first-run demonstration."""
    import random
    from datetime import timedelta

    base_time = datetime(2026, 1, 1, 10, 0, 0)
    statuses = ["COMPLETED", "PENDING", "REFUNDED", "INVALID_STATUS", "COMPLETED"]
    categories = ["electronics", "groceries", "fashion", "entertainment"]

    rows = []
    for i in range(1, row_count + 1):
        user_id = f"USR_{(i % 20) + 1:04d}"
        amount = round(random.uniform(-10.0, 500.0), 2)
        status = random.choice(statuses)
        category = random.choice(categories)
        created_at = (base_time + timedelta(hours=i)).strftime("%Y-%m-%d %H:%M:%S")
        rows.append((f"TX_{i:06d}", user_id, amount, status, category, created_at))

    return spark.createDataFrame(rows, schema=get_raw_transactions_schema())


def run_lakehouse_pipeline(
    spark: SparkSession,
    catalog: Any,
    bronze_df: Optional[DataFrame] = None,
    row_count: int = 100,
) -> Dict[str, Any]:
    """Executes the end-to-end Medallion Pipeline."""
    logger.info("Starting {{project_name}} Lakehouse Pipeline execution...")

    # 1. Ingest Bronze
    if bronze_df is None:
        logger.info("Generating %d synthetic rows for bronze layer...", row_count)
        bronze_df = generate_synthetic_bronze_data(spark, row_count=row_count)
    
    catalog.save_table(bronze_df, "transactions_bronze", mode="overwrite")
    bronze_count = bronze_df.count()
    logger.info("Bronze layer persisted (%d rows).", bronze_count)

    # 2. Process Silver
    loaded_bronze = catalog.load_table("transactions_bronze")
    silver_df = clean_transactions(loaded_bronze)
    catalog.save_table(silver_df, "transactions_silver", mode="overwrite", partition_by=["date"])
    silver_count = silver_df.count()
    logger.info("Silver layer persisted (%d rows).", silver_count)

    # 3. Aggregate Gold
    loaded_silver = catalog.load_table("transactions_silver")
    gold_df = aggregate_daily_metrics(loaded_silver)
    catalog.save_table(gold_df, "customer_daily_metrics_gold", mode="overwrite")
    gold_count = gold_df.count()
    logger.info("Gold layer persisted (%d rows).", gold_count)

    return {
        "status": "SUCCESS",
        "bronze_records": bronze_count,
        "silver_records": silver_count,
        "gold_records": gold_count,
    }
