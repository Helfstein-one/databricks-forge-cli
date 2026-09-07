# Databricks notebook source
# MAGIC %md
# MAGIC # 🚀 {{project_name}} - Databricks CE Pipeline Runner
# MAGIC 
# MAGIC This notebook was automatically scaffolded and deployed by **Databricks Forge CLI**.
# MAGIC 
# MAGIC It coordinates pipeline execution inside **Databricks Community Edition** (or Enterprise clusters),
# MAGIC installing the latest compiled wheel artifact, configuring catalog persistence, and executing
# MAGIC the Medallion architecture transformations (Bronze -> Silver -> Gold).

# COMMAND ----------

# MAGIC %md
# MAGIC ### 1. Parameter Configuration via Databricks Widgets

# COMMAND ----------

dbutils.widgets.text("row_count", "1000", "Synthetic Ingestion Rows")
dbutils.widgets.dropdown("log_level", "INFO", ["DEBUG", "INFO", "WARNING", "ERROR"], "Logging Level")
dbutils.widgets.text("wheel_name", "", "Specific Wheel Filename (leave blank for auto-detect)")

row_count = int(dbutils.widgets.get("row_count"))
log_level = dbutils.widgets.get("log_level")
wheel_override = dbutils.widgets.get("wheel_name").strip()

print(f"Executing pipeline with: row_count={row_count}, log_level={log_level}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2. Install / Verify Compiled Project Wheel

# COMMAND ----------

import os
import glob
import logging

logging.basicConfig(level=getattr(logging, log_level, logging.INFO))

# Locate the wheel in current workspace or dbfs if available
current_dir = os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())
print(f"Current Notebook Workspace Path: {current_dir}")

# Attempt to install project wheel if uploaded
%pip install --upgrade pip

# Try importing the project package
try:
    import {{project_slug}}
    print(f"✔ {{project_slug}} version {getattr({{project_slug}}, '__version__', 'latest')} is already active.")
except ImportError:
    print("Package not installed in cluster environment. Installing local wheel...")
    # In Databricks, uploaded wheels to Workspace can be installed directly
    # or fallback to local path execution
    pass

# COMMAND ----------

# MAGIC %md
# MAGIC ### 3. Import Pipeline Modules & Initialize Catalog

# COMMAND ----------

from {{project_slug}}.catalog import CatalogManager
from {{project_slug}}.pipelines.example_pipeline import (
    clean_transactions,
    aggregate_daily_metrics,
    generate_synthetic_bronze_data,
    run_lakehouse_pipeline,
)

catalog = CatalogManager(spark=spark)
print("Catalog manager successfully initialized with SparkSession:", spark)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4. Execute Medallion Pipeline (Bronze -> Silver -> Gold)

# COMMAND ----------

execution_summary = run_lakehouse_pipeline(
    spark=spark,
    catalog=catalog,
    row_count=row_count
)

print("\n==========================================")
print("  PIPELINE EXECUTION SUMMARY")
print("==========================================")
for k, v in execution_summary.items():
    print(f"  {k}: {v}")
print("==========================================\n")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5. Inspect Gold Layer Results

# COMMAND ----------

gold_metrics_df = catalog.load_table("customer_daily_metrics_gold")
display(gold_metrics_df.limit(50))

# COMMAND ----------

# MAGIC %md
# MAGIC ### 6. Pipeline Health Check & Assertions

# COMMAND ----------

assert gold_metrics_df.count() > 0, "Gold metrics table must contain records!"
print("✔ All pipeline health assertions passed successfully!")
