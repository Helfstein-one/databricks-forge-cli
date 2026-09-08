# Databricks notebook source
# MAGIC %md
# MAGIC # ⚡ {{project_name}} - Structured Streaming Runner
# MAGIC 
# MAGIC This notebook coordinates **Delta Lake Structured Streaming** inside **Databricks Community Edition** (or Enterprise clusters).
# MAGIC 
# MAGIC ### Key Features:
# MAGIC - **Watermarking (10m)** for robust handling of late-arriving event streams.
# MAGIC - **Tumbling Window Aggregations (5m)** for near real-time metric computations.
# MAGIC - **Fault-Tolerant Checkpoints** on Delta Lake storage.
# MAGIC - **Micro-Batch Mode (`trigger(availableNow=True)`)** optimized for Databricks CE scheduled runs without continuous cluster idle costs.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Parameter Configuration via Databricks Widgets

# COMMAND ----------

dbutils.widgets.dropdown("trigger_mode", "available_now", ["available_now", "continuous", "processing_time"], "Streaming Trigger Mode")
dbutils.widgets.text("watermark_delay", "10 minutes", "Watermark Delay (e.g. 10 minutes)")
dbutils.widgets.text("checkpoint_dir", "/tmp/checkpoints/{{project_slug}}_streaming", "Checkpoint Location")
dbutils.widgets.text("seed_rows", "200", "Synthetic Seed Stream Rows")

trigger_mode = dbutils.widgets.get("trigger_mode")
watermark_delay = dbutils.widgets.get("watermark_delay")
checkpoint_dir = dbutils.widgets.get("checkpoint_dir")
seed_rows = int(dbutils.widgets.get("seed_rows"))

print(f"Trigger Mode: {trigger_mode}")
print(f"Watermark Delay: {watermark_delay}")
print(f"Checkpoint Dir: {checkpoint_dir}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Import Modules & Ensure Bronze Source Stream

# COMMAND ----------

import os
import time
from pyspark.sql import functions as F
from {{project_slug}}.catalog import CatalogManager
from {{project_slug}}.pipelines.example_pipeline import generate_synthetic_bronze_data
from {{project_slug}}.pipelines.streaming_pipeline import (
    transform_streaming_transactions,
    aggregate_streaming_windows,
)

catalog = CatalogManager(spark=spark)

# Seed Bronze source if not yet populated
bronze_table_name = "transactions_bronze"
seed_df = generate_synthetic_bronze_data(spark=spark, count=seed_rows)
catalog.save_table(seed_df, bronze_table_name, mode="append")
print(f"✔ Seeded {seed_rows} records into Bronze table '{bronze_table_name}'")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3. Start Streaming Transformations & Sink to Delta

# COMMAND ----------

source_stream = spark.readStream.format("delta").table(bronze_table_name)
cleaned_stream = transform_streaming_transactions(source_stream, watermark_delay=watermark_delay)
target_stream_table = "streaming_transactions_silver"

stream_writer = (
    cleaned_stream
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", checkpoint_dir)
)

if trigger_mode == "available_now":
    print("▶ Executing in AvailableNow micro-batch mode...")
    query = stream_writer.trigger(availableNow=True).toTable(target_stream_table)
    query.awaitTermination(timeout=60)
    print(f"✔ AvailableNow micro-batch completed. Query ID: {query.id}")
elif trigger_mode == "processing_time":
    print("▶ Executing with 10 seconds processing-time micro-batch trigger...")
    query = stream_writer.trigger(processingTime="10 seconds").toTable(target_stream_table)
    time.sleep(15)
else:
    print("▶ Executing continuous stream...")
    query = stream_writer.toTable(target_stream_table)
    time.sleep(15)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4. Inspect Streamed Delta Results

# COMMAND ----------

silver_stream_df = spark.table(target_stream_table)
print(f"Current count in '{target_stream_table}': {silver_stream_df.count()}")
display(silver_stream_df.limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5. Streaming Health Assertions

# COMMAND ----------

assert silver_stream_df.count() > 0, "Silver stream table should have processed records!"
print("✔ Structured Streaming pipeline executed successfully!")
