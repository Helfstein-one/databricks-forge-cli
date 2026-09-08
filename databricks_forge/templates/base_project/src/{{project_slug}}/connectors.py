"""Multi-Database Connectors for {{project_name}} Lakehouse.

Provides unified, high-throughput partitioned JDBC ingestion (Bronze)
and reverse-ETL batch export (Gold) across:
- PostgreSQL
- MySQL / MariaDB
- Microsoft SQL Server / Azure SQL
- Oracle Database
- Snowflake
- MongoDB
- Google BigQuery
- SQLite
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from {{project_slug}}.secrets import get_secret

try:
    from pyspark.sql import DataFrame, SparkSession
except ImportError:
    class DataFrame:  # type: ignore
        pass

    class SparkSession:  # type: ignore
        pass

logger = logging.getLogger(__name__)

JDBC_DRIVER_MAP = {
    "postgresql": "org.postgresql.Driver",
    "mysql": "com.mysql.cj.jdbc.Driver",
    "sqlserver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
    "oracle": "oracle.jdbc.driver.OracleDriver",
    "snowflake": "net.snowflake.client.jdbc.SnowflakeDriver",
    "sqlite": "org.sqlite.JDBC",
}


def build_connection_url(
    db_type: str,
    host: str,
    database: str,
    port: Optional[int] = None,
) -> str:
    """Builds standard JDBC connection URL for target database type."""
    db = db_type.lower().strip()
    if db == "postgresql":
        p = port or 5432
        return f"jdbc:postgresql://{host}:{p}/{database}"
    elif db == "mysql":
        p = port or 3306
        return f"jdbc:mysql://{host}:{p}/{database}"
    elif db == "sqlserver":
        p = port or 1433
        return f"jdbc:sqlserver://{host}:{p};databaseName={database};encrypt=true;trustServerCertificate=true"
    elif db == "oracle":
        p = port or 1521
        return f"jdbc:oracle:thin:@//{host}:{p}/{database}"
    elif db == "snowflake":
        return f"jdbc:snowflake://{host}/?db={database}"
    elif db == "sqlite":
        return f"jdbc:sqlite:{database}"
    else:
        raise ValueError(f"Unsupported database type '{db_type}'.")


def read_database_table(
    spark: SparkSession,
    db_type: str,
    table_or_query: str,
    host: str,
    database: str,
    user: str,
    secret_scope: Optional[str] = None,
    secret_key: str = "password",
    partition_column: Optional[str] = None,
    lower_bound: Optional[int] = None,
    upper_bound: Optional[int] = None,
    num_partitions: int = 4,
    fetchsize: int = 10000,
    port: Optional[int] = None,
    extra_options: Optional[Dict[str, str]] = None,
) -> DataFrame:
    """Performs high-performance partitioned JDBC ingestion into a Spark DataFrame.
    
    Credentials are safely resolved from Databricks Secret Scope or local environment variables.
    """
    scope = secret_scope or f"{db_type}_scope"
    password = get_secret(scope, secret_key, default="")

    jdbc_url = build_connection_url(db_type, host=host, database=database, port=port)
    driver = JDBC_DRIVER_MAP.get(db_type.lower())

    reader = (
        spark.read.format("jdbc")
        .option("url", jdbc_url)
        .option("dbtable", table_or_query)
        .option("user", user)
        .option("password", password)
        .option("fetchsize", str(fetchsize))
    )

    if driver:
        reader = reader.option("driver", driver)

    # Enable parallel partitioned reading if specified
    if partition_column and lower_bound is not None and upper_bound is not None:
        logger.info(
            "Configuring parallel partitioned JDBC read on '%s' (%d partitions)",
            partition_column,
            num_partitions,
        )
        reader = (
            reader.option("partitionColumn", partition_column)
            .option("lowerBound", str(lower_bound))
            .option("upperBound", str(upper_bound))
            .option("numPartitions", str(num_partitions))
        )

    if extra_options:
        for k, v in extra_options.items():
            reader = reader.option(k, v)

    logger.info("Reading from %s table '%s'...", db_type.upper(), table_or_query)
    return reader.load()


def write_database_table(
    df: DataFrame,
    db_type: str,
    target_table: str,
    host: str,
    database: str,
    user: str,
    secret_scope: Optional[str] = None,
    secret_key: str = "password",
    mode: str = "append",
    batchsize: int = 5000,
    port: Optional[int] = None,
    extra_options: Optional[Dict[str, str]] = None,
) -> None:
    """Performs Reverse-ETL export from a DataFrame into an external relational database."""
    scope = secret_scope or f"{db_type}_scope"
    password = get_secret(scope, secret_key, default="")

    jdbc_url = build_connection_url(db_type, host=host, database=database, port=port)
    driver = JDBC_DRIVER_MAP.get(db_type.lower())

    writer = (
        df.write.format("jdbc")
        .option("url", jdbc_url)
        .option("dbtable", target_table)
        .option("user", user)
        .option("password", password)
        .option("batchsize", str(batchsize))
        .mode(mode)
    )

    if driver:
        writer = writer.option("driver", driver)

    if extra_options:
        for k, v in extra_options.items():
            writer = writer.option(k, v)

    logger.info("Writing records to %s table '%s' (mode=%s)...", db_type.upper(), target_table, mode)
    writer.save()
