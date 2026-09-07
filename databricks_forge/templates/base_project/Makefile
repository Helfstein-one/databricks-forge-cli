.PHONY: help install lint test unit-test integration-test perf-test docker-build docker-test run-local build deploy clean

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
	@echo "  make run-local         Execute pipeline locally"
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

build:
	python -m build --wheel --outdir dist/

deploy:
	forge deploy --target-path "/Shared/forge_deployments/{{project_slug}}" --upload-notebook

clean:
	rm -rf dist/ build/ *.egg-info .pytest_cache/ .ruff_cache/ data_lake/
	find . -type d -name "__pycache__" -exec rm -rf {} +
