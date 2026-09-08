-- ====================================================================
-- Databricks Forge CLI - Delta Lake Table Maintenance & Optimization
-- ====================================================================

-- 1. Compact small files and apply multi-dimensional clustering via Z-ORDER
OPTIMIZE transactions_silver 
ZORDER BY (user_id, date);

-- 2. Compact gold customer metrics
OPTIMIZE customer_daily_metrics_gold
ZORDER BY (user_id, date);

-- 3. Safely prune uncommitted or deleted snapshots older than 7 days (168 hours)
VACUUM transactions_silver RETAIN 168 HOURS;
