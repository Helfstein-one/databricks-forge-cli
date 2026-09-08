# Databricks notebook source
# MAGIC %md
# MAGIC # 🥇 Medallion Stage 3: Gold (Business Aggregations & KPIs)
# MAGIC Computes executive KPI summaries into `medallion_gold_sales_kpis` and `medallion_gold_customer_kpis`.

# COMMAND ----------
from pyspark.sql import functions as F

print("▶ Starting Gold Aggregations & KPI Calculation...")

source_table = "medallion_silver_transactions"
df_silver = spark.table(source_table)

# 1. Daily Category Performance KPI
df_daily_kpis = (
    df_silver
    .filter(F.col("status") == "COMPLETED")
    .groupBy("date", "category")
    .agg(
        F.round(F.sum("amount"), 2).alias("total_revenue"),
        F.count("transaction_id").alias("total_orders"),
        F.round(F.avg("amount"), 2).alias("avg_order_value"),
        F.countDistinct("user_id").alias("unique_customers"),
    )
    .sort("date", "category")
)

df_daily_kpis.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("medallion_gold_sales_kpis")

# 2. Customer VIP / Lifetime Metrics
df_customer_kpis = (
    df_silver
    .filter(F.col("status") == "COMPLETED")
    .groupBy("user_id")
    .agg(
        F.round(F.sum("amount"), 2).alias("lifetime_spend"),
        F.count("transaction_id").alias("lifetime_orders"),
        F.round(F.avg("amount"), 2).alias("avg_spend_per_order"),
    )
    .withColumn("is_vip", F.col("lifetime_spend") >= 1000.0)
    .sort(F.col("lifetime_spend").desc())
)

df_customer_kpis.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable("medallion_gold_customer_kpis")

gold_sales_count = spark.table("medallion_gold_sales_kpis").count()
gold_customer_count = spark.table("medallion_gold_customer_kpis").count()

print(f"✔ Gold Sales KPIs: {gold_sales_count} aggregates in 'medallion_gold_sales_kpis'")
print(f"✔ Gold Customer KPIs: {gold_customer_count} customers in 'medallion_gold_customer_kpis'")
display(spark.table("medallion_gold_sales_kpis").limit(10))
