# Databricks notebook source
# MAGIC %md
# MAGIC # 🥈 Medallion Stage 2: Silver (Cleaning & Quality Enforcement)
# MAGIC Standardizes, deduplicates, and validates bronze transactions into `medallion_silver_transactions`.

# COMMAND ----------
from pyspark.sql import functions as F

print("▶ Starting Silver Cleaning & Quality Validation...")

source_table = "medallion_bronze_transactions"
target_table = "medallion_silver_transactions"

df_bronze = spark.table(source_table)
initial_count = df_bronze.count()
print(f"Read {initial_count} records from Bronze.")

# Data cleansing and quality validation
valid_statuses = ["COMPLETED", "PENDING", "REFUNDED"]

df_silver = (
    df_bronze
    .dropDuplicates(["transaction_id"])
    .filter(F.col("transaction_id").isNotNull() & F.col("user_id").isNotNull())
    .filter(F.col("amount").isNotNull() & (F.col("amount") > 0.0))
    .withColumn("status", F.upper(F.trim(F.col("status"))))
    .filter(F.col("status").isin(valid_statuses))
    .withColumn("timestamp", F.to_timestamp(F.col("created_at")))
    .withColumn("date", F.to_date(F.col("timestamp")))
    .withColumn("_silver_processed_at", F.current_timestamp())
)

df_silver.write.format("delta").mode("overwrite").partitionBy("date").option("overwriteSchema", "true").saveAsTable(target_table)

silver_count = spark.table(target_table).count()
filtered_count = initial_count - silver_count
print(f"✔ Cleaned dataset persisted to '{target_table}'. Valid: {silver_count}, Filtered/Dirty: {filtered_count}")
display(spark.table(target_table).limit(5))
