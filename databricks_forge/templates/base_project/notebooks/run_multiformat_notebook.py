# Databricks notebook source
# MAGIC %md
# MAGIC # 🌐 {{project_name}} - Multi-Format & Apache Iceberg (UniForm) Runner
# MAGIC 
# MAGIC This notebook demonstrates **heterogeneous file format ingestion** (Parquet, ORC, Avro, CSV, JSON)
# MAGIC and **Delta UniForm (Universal Format)** for Apache Iceberg compatibility inside Databricks CE.
# MAGIC 
# MAGIC ### Key Capabilities:
# MAGIC - **Multi-Format Ingestion**: Ingest CSV, JSON, Parquet, Avro into a standardized PySpark DataFrame.
# MAGIC - **Delta Lake Lakehouse Sink**: ACID transactions, schema enforcement, and time travel.
# MAGIC - **Delta UniForm (Iceberg)**: Generates Apache Iceberg metadata without duplicating Parquet data files.
# MAGIC - **Open Read Interoperability**: Exposes data for Trino, Snowflake, AWS Athena, and DuckDB.

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Parameter Configuration via Widgets

# COMMAND ----------

dbutils.widgets.dropdown("source_format", "parquet", ["parquet", "csv", "json", "avro"], "Input File Format")
dbutils.widgets.dropdown("enable_uniform", "true", ["true", "false"], "Enable Delta UniForm (Iceberg)")
dbutils.widgets.text("sample_rows", "300", "Synthetic Ingestion Records")

source_format = dbutils.widgets.get("source_format")
enable_uniform = dbutils.widgets.get("enable_uniform").lower() == "true"
sample_rows = int(dbutils.widgets.get("sample_rows"))

print(f"Ingesting {sample_rows} records using format: {source_format}")
print(f"Enable Delta UniForm (Iceberg): {enable_uniform}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Generate and Persist Raw Multi-Format Source Data

# COMMAND ----------

import os
from {{project_slug}}.catalog import CatalogManager
from {{project_slug}}.pipelines.example_pipeline import generate_synthetic_bronze_data
from {{project_slug}}.formats import read_dataset, write_dataset, convert_dataset
from {{project_slug}}.iceberg import enable_delta_uniform, inspect_iceberg_metadata

raw_sample_df = generate_synthetic_bronze_data(spark=spark, count=sample_rows)
raw_storage_path = f"/tmp/{{project_slug}}_raw_data.{source_format}"

# Persist in raw format
write_dataset(
    df=raw_sample_df,
    path_or_table=raw_storage_path,
    format=source_format,
    mode="overwrite",
)
print(f"✔ Successfully wrote raw {source_format} data to {raw_storage_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3. Ingest Multi-Format Dataset into Delta Lake Silver

# COMMAND ----------

ingested_df = read_dataset(
    spark=spark,
    path_or_table=raw_storage_path,
    format=source_format,
)
print(f"Loaded {ingested_df.count()} rows from {source_format} file.")

silver_target_table = "multiformat_transactions_silver"
write_dataset(
    df=ingested_df,
    path_or_table=silver_target_table,
    format="delta",
    mode="overwrite",
    partition_by=["category"],
)
print(f"✔ Persisted into Delta Lake table '{silver_target_table}' partitioned by category.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4. Activate Apache Iceberg UniForm Compatibility

# COMMAND ----------

if enable_uniform:
    print(f"Activating Delta UniForm (Iceberg) on '{silver_target_table}'...")
    uniform_result = enable_delta_uniform(spark=spark, table_name=silver_target_table)
    print("UniForm Activation Result:", uniform_result)
else:
    print("Delta UniForm was skipped.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5. Query Results & Verify Assertions

# COMMAND ----------

result_df = spark.table(silver_target_table)
display(result_df.limit(25))

assert result_df.count() == sample_rows, f"Expected {sample_rows} rows, got {result_df.count()}"
print(f"✔ Multi-format ingestion and Iceberg compatibility validated successfully for {source_format}!")
