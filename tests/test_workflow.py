"""Tests for multi-job DAG workflow orchestrator."""

from pathlib import Path
import pytest
from databricks_forge.core.compute import ComputeConfig
from databricks_forge.core.workflow import (
    DAGWorkflow,
    DAGTask,
    DAGCycleError,
    DAGValidationError,
)


def test_dag_validation_success():
    wf = DAGWorkflow(
        name="test_lakehouse_dag",
        compute=ComputeConfig(cloud="aws", node_type_id="i3.xlarge"),
        tasks=[
            DAGTask(name="task_a", task_type="python_wheel"),
            DAGTask(name="task_b", task_type="sql", depends_on=["task_a"]),
            DAGTask(name="task_c", task_type="notebook", depends_on=["task_b"]),
        ]
    )
    order = wf.validate_dag()
    assert order == ["task_a", "task_b", "task_c"]


def test_dag_cycle_detection():
    wf = DAGWorkflow(
        name="cycle_dag",
        compute=ComputeConfig(),
        tasks=[
            DAGTask(name="task_1", task_type="python_wheel", depends_on=["task_3"]),
            DAGTask(name="task_2", task_type="sql", depends_on=["task_1"]),
            DAGTask(name="task_3", task_type="notebook", depends_on=["task_2"]),
        ]
    )
    with pytest.raises(DAGCycleError, match="Circular dependency detected"):
        wf.validate_dag()


def test_dag_unknown_dependency():
    wf = DAGWorkflow(
        name="bad_dep_dag",
        compute=ComputeConfig(),
        tasks=[
            DAGTask(name="task_1", task_type="python_wheel", depends_on=["non_existent_task"]),
        ]
    )
    with pytest.raises(DAGValidationError, match="depends on unknown task"):
        wf.validate_dag()


def test_to_databricks_jobs_api_payload():
    wf = DAGWorkflow(
        name="jobs_api_dag",
        compute=ComputeConfig(cloud="aws", node_type_id="i3.xlarge", num_workers=2),
        tasks=[
            DAGTask(name="step_ingest", task_type="python_wheel", entrypoint="pkg.ingest:main"),
            DAGTask(name="step_sql", task_type="sql", depends_on=["step_ingest"], file="sql/clean.sql"),
        ]
    )
    payload = wf.to_databricks_jobs_api_payload(workspace_base_path="/Shared/prod")
    assert payload["name"] == "jobs_api_dag"
    assert len(payload["job_clusters"]) == 1
    assert payload["job_clusters"][0]["new_cluster"]["node_type_id"] == "i3.xlarge"
    assert len(payload["tasks"]) == 2
    assert payload["tasks"][1]["task_key"] == "step_sql"
    assert payload["tasks"][1]["depends_on"] == [{"task_key": "step_ingest"}]


def test_generate_ce_master_runner(tmp_path: Path):
    wf = DAGWorkflow(
        name="ce_dag",
        compute=ComputeConfig(cloud="ce"),
        tasks=[
            DAGTask(name="step1", task_type="python_wheel"),
            DAGTask(name="step2", task_type="sql", depends_on=["step1"]),
        ]
    )
    nb_path = tmp_path / "master_dag_runner.py"
    res = wf.generate_ce_master_runner(nb_path)
    assert res.exists()
    content = res.read_text()
    assert "# Databricks notebook source" in content
    assert "Step 1: Task `step1`" in content
    assert "Step 2: Task `step2`" in content
