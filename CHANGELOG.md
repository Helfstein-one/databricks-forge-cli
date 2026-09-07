# Changelog

All notable changes to the **Databricks Forge CLI** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-09-07

### Added
- **Core CLI Engine**:
  - `forge init <project_name>`: Jinja2-based scaffolding generator for production-ready PySpark Lakehouse projects.
  - `forge build`: High-speed Wheel packaging utility compiling distribution `.whl` artifacts.
  - `forge deploy`: Databricks Community Edition (CE) deployment synchronizer using the Workspace REST API (`/api/2.0/workspace/import`).
  - `forge run-notebook`: Databricks CE runner coordinator, generating direct workspace links and interactive execution instructions.
  - `forge check`: Environment diagnostics tool validating local Python, Java Runtime, Container Engine (Docker/Podman), and Databricks API credentials.
- **Scaffolded Project Template (`base_project`)**:
  - **Hybrid Runtime Abstraction (`session.py`)**: Seamless switching between local PySpark Delta Lake and remote Databricks Connect v2.
  - **Catalog Abstraction Layer (`catalog.py`)**: Unified `CatalogManager` supporting local filesystem Delta tables and remote Databricks Metastore / Unity Catalog.
  - **Medallion Pipeline Pattern (`example_pipeline.py`)**: Multi-hop architecture processing Bronze (raw) -> Silver (cleansed) -> Gold (aggregated metrics) with audit columns.
  - **Databricks CE Runner Notebook (`run_pipeline_notebook.py`)**: Native Databricks source notebook format with interactive Widgets (`row_count`, `log_level`, `wheel_name`), automated `.whl` installation, and assertion reports.
  - **Containerized Environment (`docker/Dockerfile` & `docker-compose.yml`)**: Debian Bullseye container with OpenJDK 11, PySpark 3.5, Delta Lake 3.0, Chispa, and volume mapping for local lakehouse storage.
  - **Testing Infrastructure**:
    - Unit tests using **Chispa** (`assert_df_equality`) for exact schema and data validations.
    - Integration tests validating `CatalogManager` persistence and partitioning.
    - Performance benchmarks with `pytest-benchmark` measuring transformation throughput.
  - **Automated CI/CD esteira**:
    - `.github/workflows/ci.yml`: Ruff linting, OpenJDK 11 test runner, and Wheel artifact build.
    - `.github/workflows/cd.yml`: Automated deployment to Databricks CE upon push to `main`.
  - **Developer Automation**:
    - `Makefile` with targets (`install`, `lint`, `unit-test`, `integration-test`, `perf-test`, `docker-test`, `run-local`, `build`, `deploy`).
    - Config templates (`local_config.yaml`, `databricks_ce.yaml`, `.env.example`).
- **Architectural Diagrams**:
  - `docs/architecture.drawio`: Complete XML solution blueprint for Draw.io.
  - `docs/architecture.svg`: Vector graphic illustrating the local workstation, GitHub Actions esteira, and Databricks CE lifecycle.
  - `assets/hero_banner.png`: High-definition project hero banner.
