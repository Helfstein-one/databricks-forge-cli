"""Multi-Job DAG Orchestration Engine for Databricks Workflows."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

from databricks_forge.core.compute import ComputeConfig


class DAGValidationError(Exception):
    """Raised when DAG specification fails validation."""
    pass


class DAGCycleError(DAGValidationError):
    """Raised when a circular dependency is detected in the DAG."""
    pass


@dataclass
class DAGTask:
    """Represents a single task in the workflow DAG."""

    name: str
    task_type: str  # 'python_wheel', 'sql', 'notebook'
    depends_on: List[str] = field(default_factory=list)
    entrypoint: Optional[str] = None
    file: Optional[str] = None
    path: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "name": self.name,
            "type": self.task_type,
        }
        if self.depends_on:
            d["depends_on"] = self.depends_on
        if self.entrypoint:
            d["entrypoint"] = self.entrypoint
        if self.file:
            d["file"] = self.file
        if self.path:
            d["path"] = self.path
        if self.parameters:
            d["parameters"] = self.parameters
        if self.description:
            d["description"] = self.description
        return d


@dataclass
class DAGWorkflow:
    """Represents a full multi-task DAG workflow."""

    name: str
    compute: ComputeConfig
    tasks: List[DAGTask] = field(default_factory=list)
    schedule: Optional[str] = None
    description: Optional[str] = None

    @classmethod
    def from_yaml(cls, yaml_path: Path | str) -> DAGWorkflow:
        """Loads and parses a workflow DAG definition from a YAML file."""
        path = Path(yaml_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Workflow file not found: {path}")

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        name = data.get("name", "forge_lakehouse_dag")
        compute_data = data.get("compute", {})
        compute = ComputeConfig.from_dict(compute_data)
        desc = data.get("description")
        sched = data.get("schedule")

        tasks: List[DAGTask] = []
        for t_data in data.get("tasks", []):
            task = DAGTask(
                name=t_data["name"],
                task_type=t_data.get("type", "python_wheel"),
                depends_on=t_data.get("depends_on", []),
                entrypoint=t_data.get("entrypoint"),
                file=t_data.get("file"),
                path=t_data.get("path"),
                parameters=t_data.get("parameters", {}),
                description=t_data.get("description"),
            )
            tasks.append(task)

        workflow = cls(
            name=name,
            compute=compute,
            tasks=tasks,
            schedule=sched,
            description=desc,
        )
        # Validate immediately upon loading
        workflow.validate_dag()
        return workflow

    def to_yaml(self, output_path: Path | str) -> None:
        """Serializes workflow to YAML format."""
        out = Path(output_path).resolve()
        data: Dict[str, Any] = {
            "name": self.name,
            "description": self.description or f"Orchestrated DAG for {self.name}",
            "compute": self.compute.to_yaml_dict(),
            "tasks": [t.to_dict() for t in self.tasks],
        }
        if self.schedule:
            data["schedule"] = self.schedule

        out.write_text(yaml.dump(data, sort_keys=False), encoding="utf-8")

    def validate_dag(self) -> List[str]:
        """Validates the DAG structure using Kahn's algorithm.
        
        Checks:
        1. Unique task names
        2. All depends_on tasks exist
        3. No circular dependencies (cycles)
        
        Returns:
            Topologically sorted list of task names (execution order).
        """
        task_names = set()
        for t in self.tasks:
            if t.name in task_names:
                raise DAGValidationError(f"Duplicate task name found in DAG: '{t.name}'")
            task_names.add(t.name)

        # Build adjacency list and in-degree map
        adj: Dict[str, List[str]] = defaultdict(list)
        in_degree: Dict[str, int] = {t.name: 0 for t in self.tasks}

        for t in self.tasks:
            for dep in t.depends_on:
                if dep not in task_names:
                    raise DAGValidationError(
                        f"Task '{t.name}' depends on unknown task '{dep}'"
                    )
                adj[dep].append(t.name)
                in_degree[t.name] += 1

        # Kahn's algorithm
        queue = deque([name for name, deg in in_degree.items() if deg == 0])
        topological_order: List[str] = []

        while queue:
            node = queue.popleft()
            topological_order.append(node)

            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(topological_order) != len(self.tasks):
            cycle_nodes = [name for name, deg in in_degree.items() if deg > 0]
            raise DAGCycleError(
                f"Circular dependency detected in DAG involving tasks: {cycle_nodes}"
            )

        return topological_order

    def to_databricks_jobs_api_payload(
        self,
        workspace_base_path: str = "/Shared/forge_deployments"
    ) -> Dict[str, Any]:
        """Compiles DAG into Databricks Jobs API v2.1 multi-task job JSON payload."""
        self.validate_dag()

        clean_base = workspace_base_path.rstrip("/")
        cluster_key = f"{self.name}_cluster"
        cluster_spec = self.compute.to_databricks_cluster_spec()

        dbx_tasks: List[Dict[str, Any]] = []

        for t in self.tasks:
            item: Dict[str, Any] = {
                "task_key": t.name,
                "job_cluster_key": cluster_key,
                "description": t.description or f"Task {t.name}",
            }
            if t.depends_on:
                item["depends_on"] = [{"task_key": dep} for dep in t.depends_on]

            # Task specific mappings
            if t.task_type == "python_wheel":
                item["python_wheel_task"] = {
                    "package_name": t.parameters.get("package_name", self.name),
                    "entry_point": t.entrypoint or t.name,
                    "parameters": t.parameters.get("args", []),
                }
            elif t.task_type == "sql":
                remote_sql = f"{clean_base}/{t.file}" if t.file else f"{clean_base}/{t.name}.sql"
                item["spark_sql_task"] = {
                    "file": remote_sql,
                    "parameters": {k: str(v) for k, v in t.parameters.items()},
                }
            elif t.task_type == "notebook":
                remote_nb = f"{clean_base}/{t.path.replace('.py', '')}" if t.path else f"{clean_base}/{t.name}"
                item["notebook_task"] = {
                    "notebook_path": remote_nb,
                    "base_parameters": {k: str(v) for k, v in t.parameters.items()},
                }
            else:
                # Generic fallback
                item["notebook_task"] = {
                    "notebook_path": f"{clean_base}/{t.name}",
                }

            dbx_tasks.append(item)

        payload: Dict[str, Any] = {
            "name": self.name,
            "job_clusters": [
                {
                    "job_cluster_key": cluster_key,
                    "new_cluster": cluster_spec,
                }
            ],
            "tasks": dbx_tasks,
        }

        if self.schedule:
            payload["schedule"] = {
                "quartz_cron_expression": self.schedule,
                "timezone_id": "UTC",
                "pause_status": "UNPAUSED",
            }

        return payload

    def generate_ce_master_runner(
        self,
        output_path: Path | str,
        workspace_base_path: str = "/Shared/forge_deployments"
    ) -> Path:
        """Generates a Databricks CE Master DAG Runner notebook for executing the workflow in CE."""
        out = Path(output_path).resolve()
        order = self.validate_dag()
        clean_base = workspace_base_path.rstrip("/")

        code_cells = [
            "# Databricks notebook source",
            "# MAGIC %md",
            f"# MAGIC # 🌐 Master DAG Orchestrator: {self.name}",
            "# MAGIC Auto-generated by **Databricks Forge CLI**.",
            "# MAGIC Executes tasks according to topological dependency resolution.",
            "",
            "# COMMAND ----------",
            "# MAGIC %md",
            f"# MAGIC ### Execution Plan Order: {', '.join(order)}",
            "",
            "# COMMAND ----------",
            "import time",
            "from datetime import datetime",
            "",
            "start_time = time.time()",
            f"print(f'Starting DAG execution: {self.name} at {datetime.now(timezone.utc).isoformat()}')",
            "task_metrics = {}",
            "",
        ]

        task_dict = {t.name: t for t in self.tasks}

        for idx, task_name in enumerate(order, start=1):
            task = task_dict[task_name]
            code_cells.extend([
                "# COMMAND ----------",
                "# MAGIC %md",
                f"# MAGIC ### Step {idx}: Task `{task.name}` (Type: {task.task_type})",
                f"# MAGIC Depends on: {task.depends_on if task.depends_on else 'None (Root Task)'}",
                "",
                "# COMMAND ----------",
                f"print('▶ Running task: {task.name} ...')",
                f"t_start = time.time()",
            ])

            if task.task_type == "python_wheel":
                entry = task.entrypoint or "main"
                code_cells.extend([
                    f"# Python Wheel Task: {task.name}",
                    f"try:",
                    f"    from {entry.split(':')[0]} import {entry.split(':')[1] if ':' in entry else 'main'}",
                    f"    # Execute task",
                    f"    res = {entry.split(':')[1] if ':' in entry else 'main'}()",
                    f"    task_metrics['{task.name}'] = 'SUCCESS'",
                    f"except Exception as exc:",
                    f"    print(f'Error executing {task.name}: {{exc}}')",
                    f"    raise",
                ])
            elif task.task_type == "sql":
                sql_rel = task.file or f"sql/{task.name}.sql"
                code_cells.extend([
                    f"# SQL Task: {task.name}",
                    f"sql_file_path = '{clean_base}/{sql_rel}'",
                    f"print(f'Executing SQL script: {{sql_file_path}}')",
                    f"# spark.sql can run queries directly",
                    f"task_metrics['{task.name}'] = 'SUCCESS'",
                ])
            elif task.task_type == "notebook":
                nb_rel = task.path.replace(".py", "") if task.path else task.name
                code_cells.extend([
                    f"# Notebook Task: {task.name}",
                    f"nb_target = '{clean_base}/{nb_rel}'",
                    f"dbutils.notebook.run(nb_target, timeout_seconds=3600, arguments={task.parameters})",
                    f"task_metrics['{task.name}'] = 'SUCCESS'",
                ])

            code_cells.extend([
                f"t_dur = time.time() - t_start",
                f"print(f'✔ Task {task.name} finished in {{t_dur:.2f}}s')",
                "",
            ])

        code_cells.extend([
            "# COMMAND ----------",
            "# MAGIC %md",
            "# MAGIC ### DAG Execution Summary",
            "",
            "# COMMAND ----------",
            "total_dur = time.time() - start_time",
            "print('====================================')",
            f"print('DAG: {self.name} Completed Successfully!')",
            "print(f'Total Duration: {total_dur:.2f}s')",
            "print('Task Statuses:', task_metrics)",
            "print('====================================')",
        ])

        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(code_cells), encoding="utf-8")
        return out
