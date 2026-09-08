# Databricks notebook source
# MAGIC %md
# MAGIC # 🥉 Medallion Stage 1: Bronze (Raw Ingestion)
# MAGIC Ingests raw event records into Delta Lake table `medallion_bronze_transactions`.

# COMMAND ----------
import random
from datetime import datetime, timedelta
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
from pyspark.sql.functions import current_timestamp

print("▶ Starting Raw Bronze Ingestion...")

schema = StructType([
    StructField("transaction_id", StringType(), False),
    StructField("user_id", StringType(), False),
    StructField("amount", DoubleType(), True),
    StructField("status", StringType(), True),
    StructField("category", StringType(), True),
    StructField("created_at", StringType(), True),
])

base_date = datetime(2026, 9, 1, 8, 0, 0)
statuses = ["COMPLETED", "COMPLETED", "PENDING", "REFUNDED", "INVALID"]
categories = ["electronics", "groceries", "fashion", "books", "home"]

data = []
for i in range(1, 151):
    u_id = f"USR_{random.randint(1, 30):04d}"
    amt = round(random.uniform(10.0, 750.0), 2) if i % 10 != 0 else -50.0
    st = random.choice(statuses) if i % 15 != 0 else None
    cat = random.choice(categories)
    ts = (base_date + timedelta(hours=i * 2)).strftime("%Y-%m-%d %H:%M:%S")
    data.append((f"TX_{i:05d}", u_id, amt, st, cat, ts))

df_raw = spark.createDataFrame(data, schema=schema)
df_raw = df_raw.withColumn("_ingested_at", current_timestamp())

table_name = "medallion_bronze_transactions"
df_raw.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(table_name)

bronze_count = spark.table(table_name).count()
print(f"✔ Successfully saved {bronze_count} records into '{table_name}'.")
display(spark.table(table_name).limit(5))
