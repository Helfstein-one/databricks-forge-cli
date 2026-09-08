"""Tests for the ProjectGenerator template rendering engine."""

from pathlib import Path
import pytest
from databricks_forge.core.generator import ProjectGenerator, slugify


def test_slugify():
    assert slugify("My Cool Lakehouse") == "my_cool_lakehouse"
    assert slugify("customer-360_pipeline") == "customer_360_pipeline"
    assert slugify("123numbers") == "proj_123numbers"
    assert slugify("Special @#$ Characters!") == "special_characters"


def test_project_generator_renders_template(tmp_path: Path):
    generator = ProjectGenerator()
    project_name = "test-lakehouse-pipeline"
    target_dir = tmp_path / project_name

    generated_files = generator.create(
        project_name=project_name,
        target_dir=target_dir,
        description="A custom lakehouse test description",
        author_name="Test Author",
        author_email="test@example.com",
    )

    assert len(generated_files) > 10
    assert target_dir.exists()

    slug = "test_lakehouse_pipeline"

    # Verify key files exist
    expected_rel_paths = [
        "pyproject.toml",
        "Makefile",
        ".env.example",
        "workflow.yaml",
        "docker/Dockerfile",
        "docker/docker-compose.yml",
        "config/local_config.yaml",
        "config/databricks_ce.yaml",
        "sql/01_clean_transactions.sql",
        "sql/02_gold_metrics.sql",
        f"src/{slug}/__init__.py",
        f"src/{slug}/session.py",
        f"src/{slug}/catalog.py",
        f"src/{slug}/secrets.py",
        f"src/{slug}/pipelines/__init__.py",
        f"src/{slug}/pipelines/example_pipeline.py",
        f"src/{slug}/entrypoint.py",
        "notebooks/run_pipeline_notebook.py",
        "notebooks/master_dag_runner.py",
        "tests/conftest.py",
        "tests/unit/test_transforms.py",
        "tests/integration/test_catalog.py",
        "tests/performance/test_throughput.py",
        ".github/workflows/ci.yml",
        ".github/workflows/cd.yml",
    ]

    for rel_path in expected_rel_paths:
        file_path = target_dir / rel_path
        assert file_path.exists(), f"Expected file not found: {rel_path}"

    # Verify no unrendered .jinja files remain in output
    for path in generated_files:
        assert not path.name.endswith(".jinja"), f"Found unrendered .jinja file: {path}"

    # Check pyproject.toml rendered content
    pyproject_content = (target_dir / "pyproject.toml").read_text()
    assert 'name = "test_lakehouse_pipeline"' in pyproject_content
    assert 'author = "Test Author"' not in pyproject_content # schema uses table
    assert 'Test Author' in pyproject_content
    assert 'test@example.com' in pyproject_content
    assert 'A custom lakehouse test description' in pyproject_content

    # Check session.py rendered content
    session_content = (target_dir / f"src/{slug}/session.py").read_text()
    assert "test-lakehouse-pipeline-Pipeline" in session_content
    assert "{{project_slug}}" not in session_content

    # Check runner notebook content
    nb_content = (target_dir / "notebooks/run_pipeline_notebook.py").read_text()
    assert f"from {slug}.catalog import CatalogManager" in nb_content
    assert "{{project_slug}}" not in nb_content
