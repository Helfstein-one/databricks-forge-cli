-- ====================================================================
-- Databricks Forge CLI - Delta UniForm (Apache Iceberg Compatibility)
-- ====================================================================
-- This script enables automatic Apache Iceberg metadata generation on
-- Delta Lake tables, allowing Trino, Snowflake, AWS Athena, and DuckDB
-- to read the tables with zero data duplication.

-- 1. Enable column mapping and UniForm Iceberg on Silver transactions
ALTER TABLE transactions_silver SET TBLPROPERTIES (
  'delta.columnMapping.mode' = 'name',
  'delta.universalFormat.enabledFormats' = 'iceberg'
);

-- 2. Trigger metadata generation via OPTIMIZE
OPTIMIZE transactions_silver;

-- 3. Enable column mapping and UniForm Iceberg on Gold customer metrics
ALTER TABLE customer_daily_metrics_gold SET TBLPROPERTIES (
  'delta.columnMapping.mode' = 'name',
  'delta.universalFormat.enabledFormats' = 'iceberg'
);

OPTIMIZE customer_daily_metrics_gold;
