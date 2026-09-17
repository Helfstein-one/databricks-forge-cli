from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, col, when, lit

def run_pipeline(spark=None):
    if spark is None:
        spark = SparkSession.builder.getOrCreate()

    # @pipeline_audit_step(step_name="load_bronze")
    bronze_raw_transactions = spark.read.format("parquet").load("bronze_raw_transactions")

    # @pipeline_audit_step(step_name="transform_bronze")
    bronze_raw_transactions = bronze_raw_transactions.withColumn("date", current_timestamp().cast("date"))
    bronze_raw_transactions = bronze_raw_transactions.withColumn("hour", current_timestamp().cast("int"))
    bronze_raw_transactions = bronze_raw_transactions.withColumn("amount", when(col("amount").isNull(), 0).otherwise(col("amount")))
    bronze_raw_transactions = bronze_raw_transactions.dropDuplicates(["id", "date", "hour", "amount"])

    # @pipeline_audit_step(step_name="transform_bronze")
    bronze_raw_transactions = bronze_raw_transactions.withColumn("_computed_at", current_timestamp())
    bronze_raw_transactions = bronze_raw_transactions.withColumn("type", when(col("type").isNull(), "unknown").otherwise(col("type")))

    # @pipeline_audit_step(step_name="write_silver")
    silver_transactions = bronze_raw_transactions.format("delta").mode("append").write.save("silver_transactions")

    spark.stop()

run_pipeline()