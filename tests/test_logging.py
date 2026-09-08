"""Tests for structured logging and audit module."""

import importlib.util
import json
import logging
from pathlib import Path
import pytest

logging_module_path = (
    Path(__file__).parent.parent
    / "databricks_forge"
    / "templates"
    / "base_project"
    / "src"
    / "{{project_slug}}"
    / "logging.py"
)
spec = importlib.util.spec_from_file_location("template_logging", logging_module_path)
template_logging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(template_logging)

StructuredJsonFormatter = template_logging.StructuredJsonFormatter
setup_pipeline_logging = template_logging.setup_pipeline_logging
pipeline_audit_step = template_logging.pipeline_audit_step


def test_structured_json_formatter():
    formatter = StructuredJsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=42,
        msg="Sample message with %s",
        args=("parameter",),
        exc_info=None,
    )
    record.step = "bronze_clean"
    record.duration_ms = 123.45

    output = formatter.format(record)
    data = json.loads(output)

    assert data["level"] == "INFO"
    assert data["logger"] == "test_logger"
    assert data["message"] == "Sample message with parameter"
    assert data["step"] == "bronze_clean"
    assert data["duration_ms"] == 123.45
    assert "timestamp" in data


def test_setup_pipeline_logging():
    test_logger = setup_pipeline_logging(level="DEBUG", json_format=True, logger_name="forge_test_logger")
    assert test_logger.level == logging.DEBUG
    assert len(test_logger.handlers) == 1
    assert isinstance(test_logger.handlers[0].formatter, StructuredJsonFormatter)


def test_pipeline_audit_step_success():
    @pipeline_audit_step("test_step")
    def sample_func(x, y):
        return x + y

    result = sample_func(10, 20)
    assert result == 30


def test_pipeline_audit_step_failure():
    @pipeline_audit_step("failing_step")
    def failing_func():
        raise ValueError("Intentional error for testing")

    with pytest.raises(ValueError, match="Intentional error for testing"):
        failing_func()
