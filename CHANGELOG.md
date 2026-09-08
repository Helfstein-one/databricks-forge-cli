# Changelog

All notable changes to the **Databricks Forge CLI** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.4.0] - 2026-09-07

### Added
- **Multi-Format Data Engine (Parquet, ORC, Avro, CSV, JSON, Delta)**:
  - `databricks_forge.core.formats`: Core format detection, conversion planner, and CLI backend.
  - `src/{{project_slug}}/formats.py`: Robust data abstraction functions:
    - `read_dataset(spark, path_or_table, format='auto', options=...)`: Ingests files or catalog tables with format auto-detection and permissive error modes.
    - `write_dataset(df, path_or_table, format='delta', mode='overwrite', partition_by=...)`: Persists data in any supported open format.
    - `convert_dataset(spark, source, target, from_format, to_format, ...)`: Direct file-to-file and table-to-table conversion pipeline.
  - CLI commands under `forge data`:
    - `forge data convert <source> <target> [--from <fmt>] [--to <fmt>] [--partition-by <cols>]`: Generates conversion execution plan.
    - `forge data inspect <path_or_table>`: Inspects inferred format, file size, partition count, and Delta log presence.
- **Apache Iceberg & Delta UniForm (Universal Format) Integration**:
  - `databricks_forge.core.iceberg`: Iceberg DDL generator, UniForm property enabler, and snapshot history query builder.
  - `src/{{project_slug}}/iceberg.py`:
    - `enable_delta_uniform(spark, table_name)`: Activates Delta UniForm Iceberg metadata generation with `delta.columnMapping.mode = 'name'`.
    - `read_iceberg_table(spark, table, as_of_snapshot_id=..., as_of_timestamp=...)`: Reads Iceberg tables with point-in-time time travel.
    - `write_iceberg_table(df, table_name, mode=...)`: Persists native Apache Iceberg tables.
    - `inspect_iceberg_metadata(spark, table_name)`: Queries recent Iceberg table snapshots and commit IDs.
  - `notebooks/run_multiformat_notebook.py`: Interactive Databricks CE runner demonstrating heterogeneous ingestion (CSV, JSON, Parquet, Avro) -> Delta Lake -> UniForm Iceberg compatibility.
  - `sql/04_iceberg_uniform.sql`: Declarative SQL script activating UniForm on Silver and Gold tables.
  - CLI commands under `forge iceberg`:
    - `forge iceberg enable-uniform <table_name>`: Generates `ALTER TABLE ... SET TBLPROPERTIES` and `OPTIMIZE` commands.
    - `forge iceberg inspect <table_name>`: Inspects metadata paths and compatibility with external query engines (Trino, Snowflake, AWS Athena, DuckDB, Presto).
    - `forge iceberg snapshots <table_name>`: Generates snapshot history query for time-travel.
- **Template & Makefile Enhancements**:
  - `workflow.yaml.jinja`: Added `enable_iceberg_uniform` task referencing `sql/04_iceberg_uniform.sql`.
  - `Makefile`: Added `make iceberg-uniform` and `make data-convert` targets.

---

## [0.3.0] - 2026-09-07

### Added
- **Structured Streaming Engine (Delta Lake + Watermarking)**:
  - `src/{{project_slug}}/pipelines/streaming_pipeline.py`:
    - Streaming transformations with 10-minute watermarking to handle late-arriving records.
    - Tumbling window aggregations (5-minute intervals) for real-time customer and transaction analytics.
    - Fault-tolerant Delta Lake sink with checkpoint management (`_checkpoints/`).
    - Micro-batch trigger (`availableNow=True`) optimized for Databricks Community Edition and cost-effective scheduled runs without continuous cluster idle costs.
  - `notebooks/run_streaming_notebook.py`: Interactive Databricks CE runner notebook with UI widgets for trigger modes, watermark delay, and checkpoint paths.
  - `tests/unit/test_streaming.py`: Chispa and PySpark unit test suite asserting streaming transformations and tumbling window metrics.
- **Delta Lake Performance Tuning & Spark AQE Engine**:
  - `databricks_forge.core.tuning`: Core engine for generating and executing optimization queries and configuration profiles (`balanced`, `write_heavy`, `read_heavy`).
  - `src/{{project_slug}}/tuning.py`: Table optimization (`OPTIMIZE`), multi-dimensional clustering (`ZORDER BY`), and snapshot pruning (`VACUUM`).
  - `sql/03_optimize_tables.sql`: Ready-to-run SQL maintenance and clustering script for Silver and Gold Delta tables.
  - CLI commands under `forge tune`:
    - `forge tune optimize <table_name> [--zorder cols] [--profile balanced|write_heavy|read_heavy]`: Generate and execute compaction plans.
    - `forge tune vacuum <table_name> [--retention hours]`: Safely prune obsolete snapshot files.
    - `forge tune config [--profile profile]`: Inspect recommended Spark Adaptive Query Execution (AQE), auto-compaction, and dynamic partition coalescing defaults.
- **Structured Logging & Lakehouse Observability**:
  - `src/{{project_slug}}/logging.py`:
    - `StructuredJsonFormatter`: RFC-compliant ISO 8601 JSON formatter for cloud log aggregators (Datadog, CloudWatch, Google Cloud Logging).
    - `setup_pipeline_logging()`: Single-call logger initialization with JSON or standard console formatters.
    - `@pipeline_audit_step`: Execution audit decorator recording step latency, timestamp, status, error traces, and DataFrame row counts.
    - `record_audit_log()`: Persists pipeline run telemetry into a central Delta Lake audit table (`pipeline_execution_audit`).
- **Template & Makefile Enhancements**:
  - `workflow.yaml.jinja`: Integrated with streaming micro-batch tasks and Delta table optimization tasks.
  - `Makefile`: Added `make stream-run` and `make optimize` commands.

---

## [0.2.1] - 2026-09-07

### Added
- **Creative & Stylized Databricks Hero Banner**:
  - High-impact, futuristic artwork in `assets/hero_banner.png` featuring laser robotic arms forging crystalline Lakehouse data structures under the radiant crimson Databricks emblem.
- **3D Multicolor Shaded ASCII Art Banner**:
  - Isometric 3D block typography in `databricks_forge/ui/banner.py` with multi-stage gradient coloring (Databricks flame red, amber, cyber blue, and violet).
- **Multi-Tab Architecture Blueprint in Draw.io**:
  - `docs/architecture.drawio` re-architected with **3 dedicated tabs**:
    1. *1. Experiência do Usuário (Funcional)*: Step-by-step developer journey.
    2. *2. Visão de Negócio (Business & ROI)*: FinOps cost reduction (80%+ compute savings), time-to-market, and governance.
    3. *3. Visão Técnica & Cloud Architecture*: Databricks control plane, compute plane (AWS, Azure, GCP, CE), Delta storage, and CI/CD.

---

## [0.2.0] - 2026-09-07

### Added
- **Minimalist Databricks Hero Banner**:
  - Re-imagined clean Scandinavian aesthetic banner in `assets/hero_banner.png` highlighting the official Databricks red-orange logo and digital forge anvil on a matte carbon-slate background.
- **Stylized ASCII Art Banner**:
  - `DATABRICKS FORGE CLI` ASCII art rendered with Rich styling and gradients at `forge init` execution.
- **Databricks Secrets & Environment Variable Management**:
  - `databricks_forge.core.secrets`: Integration with Databricks Secrets REST API (`/api/2.0/secrets/*`).
  - CLI commands under `forge secret`:
    - `forge secret list`: List scopes or secrets within a scope.
    - `forge secret create-scope <name>`: Create secret scope in Databricks.
    - `forge secret set <scope> <key>`: Store/update encrypted secret in scope.
    - `forge secret sync-env`: Synchronize local `.env` variables directly into a Databricks Secret Scope.
  - Universal `secrets.py` in template: `get_secret(scope, key, default)` that transparently uses `dbutils.secrets.get` on Databricks clusters and `os.getenv` / `.env` locally without code branching.
- **Multi-Job DAG Orchestration Engine**:
  - `databricks_forge.core.workflow`: DAG dependency resolution using Kahn's topological sort algorithm with circular dependency detection (`DAGCycleError`).
  - `workflow.yaml`: Declarative DAG definition supporting heterogeneous tasks (`python_wheel`, `sql`, `notebook`) and dependency chains (`depends_on`).
  - CLI commands under `forge dag`:
    - `forge dag validate`: Validates graph structure, tasks, and compute specs.
    - `forge dag run`: Executes DAG tasks locally in resolved topological order.
    - `forge dag export`: Compiles DAG to native Databricks Jobs API v2.1 multi-task JSON payload.
  - `master_dag_runner.py`: Orchestrator notebook generated for Databricks Community Edition, executing multi-task DAGs with zero cloud licensing cost.
- **SQL Jobs Support**:
  - `databricks_forge.core.sql`: SQL statement parser and multi-statement runner.
  - CLI commands under `forge sql`:
    - `forge sql run <file.sql>`: Execute SQL transformations locally against Delta Lake or via Databricks Connect.
    - `forge sql deploy <file.sql>`: Deploy SQL scripts directly to Databricks Workspace (`format=SOURCE`, `language=SQL`).
  - Template SQL scripts: `sql/01_clean_transactions.sql`, `sql/02_gold_metrics.sql`.
- **Compute and Machine Catalog**:
  - `databricks_forge.core.compute`: Presets and catalogs for **AWS** (`i3.xlarge`, `m5d.large`, `c5.xlarge`, `r5.xlarge`), **Azure** (`Standard_DS3_v2`, `D4s_v5`), **GCP** (`n1-standard-4`), and **Community Edition** (`SingleNode`).
  - CLI command `forge compute list`.
  - Flags `--cloud`, `--node-type`, `--workers`, `--spark-version` in `forge init`.
- **Updated Architectural Blueprint**:
  - `docs/architecture.svg` and `docs/architecture.drawio` updated with official technology logos and the complete DAG, Secrets, and Compute workflows.

---

## [0.1.0] - 2026-09-07

### Added
- Initial release of `databricks-forge-cli`.
- Scaffolding generator (`forge init`), Wheel packaging (`forge build`), and Workspace API deploy (`forge deploy`).
- Base project template with hybrid SparkSession (`session.py`), `CatalogManager` (`catalog.py`), Medallion pipeline (`example_pipeline.py`), and runner notebook.
- Docker environment with OpenJDK 11, PySpark 3.5, and Delta Lake 3.0.
- Chispa unit tests and pytest-benchmark tests.
- GitHub Actions CI/CD workflows.
