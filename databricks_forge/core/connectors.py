"""Core database connectors catalog, JDBC URL generators, and ingestion planners."""

from __future__ import annotations

import logging
import socket
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DATABASE_CATALOG: Dict[str, Dict[str, Any]] = {
    "postgresql": {
        "name": "PostgreSQL",
        "category": "Relational (RDBMS)",
        "default_port": 5432,
        "driver_class": "org.postgresql.Driver",
        "maven_package": "org.postgresql:postgresql:42.7.2",
        "url_template": "jdbc:postgresql://{host}:{port}/{database}",
        "url_example": "jdbc:postgresql://postgres.example.com:5432/ecommerce_db",
        "dialect": "PostgreSQL",
    },
    "mysql": {
        "name": "MySQL / MariaDB",
        "category": "Relational (RDBMS)",
        "default_port": 3306,
        "driver_class": "com.mysql.cj.jdbc.Driver",
        "maven_package": "com.mysql:mysql-connector-j:8.3.0",
        "url_template": "jdbc:mysql://{host}:{port}/{database}",
        "url_example": "jdbc:mysql://mysql.example.com:3306/production_db",
        "dialect": "MySQL",
    },
    "sqlserver": {
        "name": "Microsoft SQL Server / Azure SQL",
        "category": "Relational (RDBMS)",
        "default_port": 1433,
        "driver_class": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
        "maven_package": "com.microsoft.sqlserver:mssql-jdbc:12.6.1.jre11",
        "url_template": "jdbc:sqlserver://{host}:{port};databaseName={database};encrypt=true;trustServerCertificate=true",
        "url_example": "jdbc:sqlserver://sqlserver.database.windows.net:1433;databaseName=erp_db",
        "dialect": "Microsoft SQL Server",
    },
    "oracle": {
        "name": "Oracle Database",
        "category": "Relational (RDBMS)",
        "default_port": 1521,
        "driver_class": "oracle.jdbc.driver.OracleDriver",
        "maven_package": "com.oracle.database.jdbc:ojdbc8:23.3.0.23.09",
        "url_template": "jdbc:oracle:thin:@//{host}:{port}/{database}",
        "url_example": "jdbc:oracle:thin:@//oracle.example.com:1521/ORCLPDB1",
        "dialect": "Oracle",
    },
    "snowflake": {
        "name": "Snowflake Cloud Data Warehouse",
        "category": "Cloud Data Warehouse",
        "default_port": 443,
        "driver_class": "net.snowflake.client.jdbc.SnowflakeDriver",
        "maven_package": "net.snowflake:spark-snowflake_2.12:2.12.0-spark_3.4",
        "url_template": "jdbc:snowflake://{host}/?db={database}",
        "url_example": "jdbc:snowflake://xy12345.snowflakecomputing.com/?db=ANALYTICS",
        "dialect": "Snowflake",
    },
    "mongodb": {
        "name": "MongoDB (Document NoSQL)",
        "category": "NoSQL Document Store",
        "default_port": 27017,
        "driver_class": "org.mongodb.spark.sql.DefaultSource",
        "maven_package": "org.mongodb.spark:mongo-spark-connector_2.12:10.2.2",
        "url_template": "mongodb://{host}:{port}/{database}",
        "url_example": "mongodb://mongo.example.com:27017/catalog_db",
        "dialect": "MongoDB",
    },
    "bigquery": {
        "name": "Google BigQuery",
        "category": "Cloud Data Warehouse",
        "default_port": 443,
        "driver_class": "com.google.cloud.spark.bigquery.DefaultSource",
        "maven_package": "com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.36.1",
        "url_template": "bigquery://{database}",
        "url_example": "bigquery://my-gcp-project.my_dataset",
        "dialect": "Google BigQuery",
    },
    "sqlite": {
        "name": "SQLite (Local / Offline Dev)",
        "category": "Embedded Relational",
        "default_port": 0,
        "driver_class": "org.sqlite.JDBC",
        "maven_package": "org.xerial:sqlite-jdbc:3.45.1.0",
        "url_template": "jdbc:sqlite:{database}",
        "url_example": "jdbc:sqlite:/tmp/local_test.db",
        "dialect": "SQLite",
    },
}


def get_connector_info(db_type: str) -> Dict[str, Any]:
    """Retrieves catalog metadata for a specific database connector."""
    normalized = db_type.strip().lower()
    if normalized not in DATABASE_CATALOG:
        supported = ", ".join(DATABASE_CATALOG.keys())
        raise ValueError(f"Unsupported database connector '{db_type}'. Supported connectors: {supported}")
    return DATABASE_CATALOG[normalized]


def build_jdbc_url(
    db_type: str,
    host: str,
    database: str,
    port: Optional[int] = None,
) -> str:
    """Builds a formatted JDBC connection URL for the target database."""
    info = get_connector_info(db_type)
    resolved_port = port or info["default_port"]

    if db_type == "sqlite":
        return info["url_template"].format(database=database)

    return info["url_template"].format(
        host=host,
        port=resolved_port,
        database=database,
    )


def build_ingest_plan(
    db_type: str,
    source_table: str,
    target_delta_table: str,
    host: str,
    database: str,
    user: str = "db_user",
    partition_column: Optional[str] = None,
    num_partitions: int = 4,
    fetchsize: int = 10000,
    port: Optional[int] = None,
) -> Dict[str, Any]:
    """Builds a high-performance partitioned JDBC ingestion execution plan."""
    info = get_connector_info(db_type)
    jdbc_url = build_jdbc_url(db_type, host=host, database=database, port=port)

    code_snippet = (
        f"# High-performance partitioned ingestion from {info['name']}\n"
        f"reader = (\n"
        f"    spark.read.format('jdbc')\n"
        f"    .option('url', '{jdbc_url}')\n"
        f"    .option('dbtable', '{source_table}')\n"
        f"    .option('user', '{user}')\n"
        f"    .option('password', get_secret('{db_type}_scope', 'password'))\n"
        f"    .option('driver', '{info['driver_class']}')\n"
        f"    .option('fetchsize', '{fetchsize}')\n"
    )

    if partition_column:
        code_snippet += (
            f"    .option('partitionColumn', '{partition_column}')\n"
            f"    .option('lowerBound', '1')\n"
            f"    .option('upperBound', '1000000')\n"
            f"    .option('numPartitions', '{num_partitions}')\n"
        )

    code_snippet += (
        f")\n"
        f"df = reader.load()\n"
        f"df.write.format('delta').mode('append').saveAsTable('{target_delta_table}')"
    )

    return {
        "status": "PLANNED",
        "database_type": db_type,
        "database_name": info["name"],
        "jdbc_url": jdbc_url,
        "driver_class": info["driver_class"],
        "source_table": source_table,
        "target_delta_table": target_delta_table,
        "fetchsize": fetchsize,
        "partition_column": partition_column,
        "num_partitions": num_partitions if partition_column else 1,
        "code_preview": code_snippet,
    }


def build_export_plan(
    source_delta_table: str,
    db_type: str,
    target_table: str,
    host: str,
    database: str,
    user: str = "db_user",
    mode: str = "append",
    batchsize: int = 5000,
    port: Optional[int] = None,
) -> Dict[str, Any]:
    """Builds a reverse-ETL plan to export Delta Lake Gold data to an external database."""
    info = get_connector_info(db_type)
    jdbc_url = build_jdbc_url(db_type, host=host, database=database, port=port)

    code_snippet = (
        f"# Reverse-ETL export from Delta Lake to {info['name']}\n"
        f"df = spark.table('{source_delta_table}')\n"
        f"(\n"
        f"    df.write.format('jdbc')\n"
        f"    .option('url', '{jdbc_url}')\n"
        f"    .option('dbtable', '{target_table}')\n"
        f"    .option('user', '{user}')\n"
        f"    .option('password', get_secret('{db_type}_scope', 'password'))\n"
        f"    .option('driver', '{info['driver_class']}')\n"
        f"    .option('batchsize', '{batchsize}')\n"
        f"    .mode('{mode}')\n"
        f"    .save()\n"
        f")"
    )

    return {
        "status": "PLANNED",
        "database_type": db_type,
        "database_name": info["name"],
        "jdbc_url": jdbc_url,
        "source_delta_table": source_delta_table,
        "target_table": target_table,
        "batchsize": batchsize,
        "mode": mode,
        "code_preview": code_snippet,
    }


def check_db_connectivity(
    db_type: str,
    host: str,
    port: Optional[int] = None,
    timeout_sec: int = 3,
) -> Dict[str, Any]:
    """Performs a TCP network handshake check to test database host and port reachability."""
    info = get_connector_info(db_type)
    target_port = port or info["default_port"]

    if db_type == "sqlite":
        return {
            "status": "SUCCESS",
            "db_type": db_type,
            "message": "SQLite is a local file-based database engine (no network port required).",
        }

    try:
        with socket.create_connection((host, target_port), timeout=timeout_sec):
            return {
                "status": "SUCCESS",
                "db_type": db_type,
                "host": host,
                "port": target_port,
                "message": f"Successfully connected to {info['name']} at {host}:{target_port}",
            }
    except Exception as exc:
        return {
            "status": "FAILED",
            "db_type": db_type,
            "host": host,
            "port": target_port,
            "error": str(exc),
            "message": f"Could not reach {info['name']} at {host}:{target_port}: {exc}",
        }


# Alias for backward compatibility
test_db_connectivity = check_db_connectivity
