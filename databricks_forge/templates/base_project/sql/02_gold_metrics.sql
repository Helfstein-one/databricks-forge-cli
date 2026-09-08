-- Databricks Forge SQL Job: Gold Layer Aggregation & Analytics
-- Produces daily KPIs and high-value customer flags

CREATE OR REPLACE TABLE default.{{project_slug}}_gold_sql AS
SELECT
    user_id,
    transaction_date,
    ROUND(SUM(amount), 2) AS total_spend,
    COUNT(transaction_id) AS transaction_count,
    ROUND(AVG(amount), 2) AS avg_transaction_amount,
    CASE 
        WHEN SUM(amount) >= 1000.0 THEN TRUE 
        ELSE FALSE 
    END AS is_high_value,
    CURRENT_TIMESTAMP() AS _computed_at
FROM default.{{project_slug}}_silver_sql
WHERE status = 'COMPLETED'
GROUP BY user_id, transaction_date
ORDER BY total_spend DESC;
