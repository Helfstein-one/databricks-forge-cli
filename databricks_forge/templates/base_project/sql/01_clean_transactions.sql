-- Databricks Forge SQL Job: Silver Layer Transformation
-- Cleans, deduplicates, and standardizes transactions from raw bronze

CREATE OR REPLACE TABLE default.{{project_slug}}_silver_sql AS
SELECT
    TRIM(transaction_id) AS transaction_id,
    TRIM(user_id) AS user_id,
    CAST(amount AS DOUBLE) AS amount,
    UPPER(TRIM(status)) AS status,
    LOWER(TRIM(category)) AS category,
    TO_TIMESTAMP(created_at) AS transaction_timestamp,
    TO_DATE(TO_TIMESTAMP(created_at)) AS transaction_date,
    CURRENT_TIMESTAMP() AS _ingested_at
FROM default.{{project_slug}}_bronze
WHERE transaction_id IS NOT NULL
  AND user_id IS NOT NULL
  AND CAST(amount AS DOUBLE) > 0
  AND UPPER(TRIM(status)) IN ('COMPLETED', 'PENDING', 'REFUNDED');
