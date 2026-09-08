"""Tests for streaming pipeline module structure and signatures."""

import importlib.util
from pathlib import Path

streaming_module_path = (
    Path(__file__).parent.parent
    / "databricks_forge"
    / "templates"
    / "base_project"
    / "src"
    / "{{project_slug}}"
    / "pipelines"
    / "streaming_pipeline.py"
)
spec = importlib.util.spec_from_file_location("template_streaming", streaming_module_path)
template_streaming = importlib.util.module_from_spec(spec)
spec.loader.exec_module(template_streaming)


def test_streaming_functions_exist():
    assert hasattr(template_streaming, "transform_streaming_transactions")
    assert hasattr(template_streaming, "aggregate_streaming_windows")
    assert hasattr(template_streaming, "start_streaming_pipeline")
    assert callable(template_streaming.transform_streaming_transactions)
    assert callable(template_streaming.aggregate_streaming_windows)
    assert callable(template_streaming.start_streaming_pipeline)
