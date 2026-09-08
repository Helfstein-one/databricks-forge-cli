# Changelog

All notable changes to the **Databricks Forge CLI** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
