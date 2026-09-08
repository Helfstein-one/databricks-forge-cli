.PHONY: help install lint test unit-test integration-test perf-test docker-build docker-test run-local stream-run optimize iceberg-uniform data-convert dag-validate dag-run sql-run build deploy clean

help:
	@echo "Available commands for {{project_name}}:"
	@echo "  make install           Install dependencies in editable mode"
	@echo "  make lint              Run ruff linter and format check"
	@echo "  make test              Run full test suite (unit + integration + perf)"
	@echo "  make unit-test         Run unit tests with Chispa"
	@echo "  make integration-test  Run integration tests"
	@echo "  make perf-test         Run performance benchmarks"
	@echo "  make docker-build      Build local PySpark Docker container"
	@echo "  make docker-test       Run unit tests inside Docker container"
	@echo "  make run-local         Execute batch pipeline locally"
	@echo "  make stream-run        Execute streaming micro-batch pipeline"
	@echo "  make optimize          Run Delta Lake OPTIMIZE with Z-ORDER"
	@echo "  make iceberg-uniform   Enable Delta UniForm for Apache Iceberg"
	@echo "  make data-convert      Convert datasets between Parquet, CSV, JSON, and Delta"
	@echo "  make dag-validate      Validate workflow.yaml DAG dependencies"
	@echo "  make dag-run           Execute full multi-job DAG"
	@echo "  make sql-run           Execute SQL transformation scripts"
	@echo "  make build             Compile project wheel into dist/"
	@echo "  make deploy            Deploy wheel to Databricks CE Workspace"
	@echo "  make clean             Remove temporary build/cache artifacts"

install:
	pip install -e ".[dev]"

lint:
	ruff check .
	ruff format --check .

test:
	pytest tests/ -v

unit-test:
	pytest tests/unit/ -v

integration-test:
	pytest tests/integration/ -v

perf-test:
	pytest tests/performance/ -v

docker-build:
	docker compose -f docker/docker-compose.yml build

docker-test:
	docker compose -f docker/docker-compose.yml run --rm spark-dev pytest tests/unit/ -v

run-local:
	python -m {{project_slug}}.entrypoint --mode local --rows 500

stream-run:
	python -c "from {{project_slug}}.session import get_spark; from {{project_slug}}.pipelines.streaming_pipeline import start_streaming_pipeline; spark = get_spark(); start_streaming_pipeline(spark, 'transactions_bronze', 'transactions_silver_stream', '/tmp/checkpoints', trigger_available_now=True)"

optimize:
	forge tune optimize transactions_silver --zorder user_id,date

iceberg-uniform:
	forge iceberg enable-uniform transactions_silver

data-convert:
	forge data convert data_lake/transactions_bronze.parquet data_lake/transactions_silver --from parquet --to delta

dag-validate:
	forge dag validate --file workflow.yaml

dag-run:
	forge dag run --file workflow.yaml --mode local

sql-run:
	forge sql run sql/01_clean_transactions.sql

build:
	python -m build --wheel --outdir dist/

deploy:
	forge deploy --target-path "/Shared/forge_deployments/{{project_slug}}" --upload-notebook

clean:
	rm -rf dist/ build/ *.egg-info .pytest_cache/ .ruff_cache/ data_lake/
	find . -type d -name "__pycache__" -exec rm -rf {} +
