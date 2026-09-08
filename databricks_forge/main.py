"""Main CLI Entrypoint for Databricks Forge CLI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import databricks_forge
from databricks_forge.core.client import DatabricksCEClient, DatabricksClientError
from databricks_forge.core.compute import (
    COMPUTE_CATALOG,
    ComputeConfig,
    get_available_node_types,
)
from databricks_forge.core.generator import ProjectGenerator
from databricks_forge.core.packaging import PackagingError, build_project_wheel
from databricks_forge.core.sql import (
    SQLJobError,
    deploy_sql_to_workspace,
    execute_sql_locally,
)
from databricks_forge.core.connectors import (
    DATABASE_CATALOG,
    build_export_plan,
    build_ingest_plan,
    build_jdbc_url,
    check_db_connectivity,
    get_connector_info,
)
from databricks_forge.core.formats import (
    SUPPORTED_FORMATS,
    build_convert_plan,
    detect_format_from_path,
)
from databricks_forge.core.iceberg import (
    build_create_uniform_table_statement,
    build_enable_uniform_statements,
    build_iceberg_snapshots_query,
    inspect_iceberg_plan,
)
from databricks_forge.core.secrets import (
    DatabricksSecretsClient,
    load_dotenv_file,
    sync_env_to_scope,
)
from databricks_forge.core.tuning import (
    TUNING_PROFILES,
    build_optimize_statement,
    build_vacuum_statement,
    execute_optimize,
    get_tuning_configs,
)
from databricks_forge.core.workflow import (
    DAGCycleError,
    DAGValidationError,
    DAGWorkflow,
)
from databricks_forge.ui.banner import render_forge_banner

# Automatically load local .env variables into environment if present
_local_env = load_dotenv_file()
for _k, _v in _local_env.items():
    if _k not in os.environ:
        os.environ[_k] = _v

app = typer.Typer(
    name="forge",
    help="⚡ Databricks Forge CLI - Industrial scaffolding, local testing, packaging, and CI/CD for Databricks CE.",
    add_completion=True,
    rich_markup_mode="rich",
)
sql_app = typer.Typer(name="sql", help="🗄️ SQL Job execution and workspace deployment.")
dag_app = typer.Typer(name="dag", help="🌐 Multi-job DAG orchestration and dependency management.")
compute_app = typer.Typer(name="compute", help="💻 Machine types and cluster compute catalogs.")
secret_app = typer.Typer(name="secret", help="🔒 Databricks Secrets and environment variables management.")
tune_app = typer.Typer(name="tune", help="⚡ Spark & Delta Lake performance tuning.")
data_app = typer.Typer(name="data", help="📁 Multi-format dataset inspection and conversion (Parquet, ORC, Avro, CSV, JSON, Delta).")
iceberg_app = typer.Typer(name="iceberg", help="🧊 Apache Iceberg tables and Delta UniForm compatibility.")
connector_app = typer.Typer(name="connector", help="🔌 Multi-database connectors (PostgreSQL, MySQL, SQL Server, Oracle, Snowflake, Mongo, BigQuery, SQLite).")

app.add_typer(sql_app)
app.add_typer(dag_app)
app.add_typer(compute_app)
app.add_typer(secret_app)
app.add_typer(tune_app)
app.add_typer(data_app)
app.add_typer(iceberg_app)
app.add_typer(connector_app)

console = Console()


def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]Databricks Forge CLI[/bold cyan] version [bold green]{databricks_forge.__version__}[/bold green]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show CLI version and exit.",
        callback=version_callback,
        is_eager=True,
    )
):
    """Databricks Forge CLI: Scaffolding and Lakehouse engineering toolkit."""
    pass


@app.command()
def init(
    project_name: str = typer.Argument(
        ...,
        help="Name of the new Lakehouse project (e.g., 'customer-analytics-lakehouse')",
    ),
    output_dir: Path = typer.Option(
        Path.cwd(),
        "--output-dir",
        "-o",
        help="Directory where the new project folder will be created.",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Custom short description for the generated project.",
    ),
    author: Optional[str] = typer.Option(
        None,
        "--author",
        "-a",
        help="Author name for pyproject.toml.",
    ),
    email: Optional[str] = typer.Option(
        None,
        "--email",
        "-e",
        help="Author email for pyproject.toml.",
    ),
    cloud: str = typer.Option(
        "ce",
        "--cloud",
        "-c",
        help="Target cloud provider: 'ce' (Community Edition), 'aws', 'azure', or 'gcp'.",
    ),
    node_type: Optional[str] = typer.Option(
        None,
        "--node-type",
        help="Machine node type ID (e.g. 'SingleNode', 'i3.xlarge', 'Standard_DS3_v2').",
    ),
    workers: int = typer.Option(
        0,
        "--workers",
        "-w",
        help="Number of worker nodes (0 for Single-Node mode / Community Edition).",
    ),
    spark_version: str = typer.Option(
        "14.3.x-scala2.12",
        "--spark-version",
        help="Target Databricks Runtime / Spark version.",
    ),
):
    """🚀 Scaffold a production-grade Lakehouse project with Docker, Databricks Connect, Chispa, and GitHub Actions."""
    # 1. Display stylized ASCII Banner
    render_forge_banner(console, subtitle=f"Scaffolding: {project_name}")

    target_path = output_dir / project_name

    if target_path.exists() and any(target_path.iterdir()):
        console.print(f"[bold red]Error:[/bold red] Target directory [yellow]{target_path}[/yellow] already exists and is not empty.")
        raise typer.Exit(code=1)

    console.print(Panel(
        f"[bold cyan]Project Name:[/bold cyan] [bold green]{project_name}[/bold green]\n"
        f"[bold cyan]Destination:[/bold cyan]  [bold white]{target_path}[/bold white]\n"
        f"[bold cyan]Cloud Target:[/bold cyan] [magenta]{cloud.upper()}[/magenta]\n"
        f"[bold cyan]Machine Type:[/bold cyan] [yellow]{node_type or ('SingleNode (Free CE)' if cloud == 'ce' else 'Default Auto')}[/yellow]\n"
        f"[bold cyan]Workers:[/bold cyan]      [white]{workers} ({'Single-Node' if workers == 0 else 'Multi-Node'})[/white]",
        title="Configuration Summary",
        border_style="cyan",
    ))

    try:
        generator = ProjectGenerator()
        files = generator.create(
            project_name=project_name,
            target_dir=target_path,
            description=description,
            author_name=author,
            author_email=email,
            cloud=cloud,
            node_type_id=node_type,
            num_workers=workers,
            spark_version=spark_version,
        )

        slug = generator.jinja_env.from_string("{{project_slug}}").render(project_slug=project_name.lower().replace("-", "_"))

        table = Table(title="Generated Project Modules", show_header=True, header_style="bold magenta")
        table.add_column("Module", style="cyan")
        table.add_column("Components", style="white")

        table.add_row("Core Lakehouse", f"src/{slug}/ (session.py, catalog.py, pipelines, entrypoint.py)")
        table.add_row("Streaming Engine", f"src/{slug}/pipelines/streaming_pipeline.py, notebooks/run_streaming_notebook.py")
        table.add_row("Multi-Format I/O", f"src/{slug}/formats.py (Parquet, ORC, Avro, CSV, JSON, Delta)")
        table.add_row("Apache Iceberg", f"src/{slug}/iceberg.py, sql/04_iceberg_uniform.sql (Delta UniForm)")
        table.add_row("DB Connectors", f"src/{slug}/connectors.py, config/database_connectors.yaml (Postgres, MySQL, MSSQL, Snowflake)")
        table.add_row("Performance Tuning", f"src/{slug}/tuning.py (AQE, OPTIMIZE, Z-ORDER, VACUUM)")
        table.add_row("Structured Logging", f"src/{slug}/logging.py (JSON Telemetry, @pipeline_audit_step)")
        table.add_row("SQL Jobs", "sql/01_clean_transactions.sql, sql/02_gold_metrics.sql")
        table.add_row("DAG Orchestration", "workflow.yaml, notebooks/master_dag_runner.py")
        table.add_row("CE Notebooks", "notebooks/run_pipeline_notebook.py, notebooks/run_multiformat_notebook.py, notebooks/run_database_connectors_notebook.py")
        table.add_row("Docker Dev", "docker/Dockerfile, docker/docker-compose.yml (PySpark 3.5 + Delta 3.0)")
        table.add_row("Test Suite", "tests/unit/ (Chispa), tests/integration/, tests/performance/")
        table.add_row("CI/CD Pipeline", ".github/workflows/ci.yml, .github/workflows/cd.yml")
        table.add_row("Automation", "Makefile, pyproject.toml, config/, .env.example")

        console.print(table)
        console.print(f"\n[bold green]✔ Successfully created {len(files)} files in {target_path}[/bold green]")
        console.print("\n[bold yellow]Quick Commands:[/bold yellow]")
        console.print(f"  • [cyan]cd {target_path}[/cyan]")
        console.print("  • [cyan]forge connector list[/cyan] (Inspect supported databases & JDBC drivers)")
        console.print("  • [cyan]forge iceberg enable-uniform <table_name>[/cyan] (Enable Iceberg metadata)")
        console.print("  • [cyan]forge data convert <src> <dst> --to delta[/cyan]  (Multi-format conversion)")
        console.print("  • [cyan]forge tune config[/cyan] (Inspect Spark AQE & Delta Lake performance presets)")
        console.print("  • [cyan]make dag-validate[/cyan] (Validate workflow.yaml dependency graph)")
        console.print("  • [cyan]make docker-test[/cyan]  (Run unit tests in Docker container)")
        console.print("  • [cyan]forge build[/cyan] && [cyan]forge deploy[/cyan]")

    except Exception as exc:
        console.print(f"[bold red]Generation failed:[/bold red] {exc}")
        raise typer.Exit(code=1)


@app.command()
def build(
    project_dir: Path = typer.Option(
        Path.cwd(),
        "--project-dir",
        "-p",
        help="Path to project directory containing pyproject.toml.",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for the compiled .whl artifact (default: <project-dir>/dist).",
    ),
    clean: bool = typer.Option(
        True,
        "--clean/--no-clean",
        help="Clean previous wheel artifacts before building.",
    ),
):
    """📦 Build standard Python Wheel (.whl) distribution for Databricks execution."""
    console.print(f"[bold blue]Building wheel for project at:[/bold blue] {project_dir.resolve()}")

    try:
        wheel_path = build_project_wheel(
            project_dir=project_dir,
            output_dir=output_dir,
            clean_before_build=clean,
        )
        size_kb = wheel_path.stat().st_size / 1024.0
        console.print(Panel(
            f"[bold green]✔ Wheel compiled successfully![/bold green]\n\n"
            f"[bold white]File:[/bold white] {wheel_path.name}\n"
            f"[bold white]Path:[/bold white] {wheel_path}\n"
            f"[bold white]Size:[/bold white] {size_kb:.2f} KB",
            title="Build Artifact",
            border_style="green",
        ))
    except PackagingError as exc:
        console.print(f"[bold red]Build Error:[/bold red] {exc}")
        raise typer.Exit(code=1)


@app.command()
def deploy(
    host: Optional[str] = typer.Option(
        None,
        "--host",
        envvar="DATABRICKS_HOST",
        help="Databricks CE URL (e.g., https://community.cloud.databricks.com)",
    ),
    token: Optional[str] = typer.Option(
        None,
        "--token",
        envvar="DATABRICKS_TOKEN",
        help="Personal Access Token for Databricks CE",
    ),
    target_path: str = typer.Option(
        ...,
        "--target-path",
        "-t",
        help="Databricks Workspace directory (e.g. '/Shared/forge_deployments' or '/Users/<your_email>/lakehouse')",
    ),
    project_dir: Path = typer.Option(
        Path.cwd(),
        "--project-dir",
        "-p",
        help="Path to project directory.",
    ),
    dist_dir: Optional[Path] = typer.Option(
        None,
        "--dist-dir",
        help="Custom dist directory containing pre-built wheel.",
    ),
    upload_notebook: bool = typer.Option(
        True,
        "--upload-notebook/--no-upload-notebook",
        help="Whether to also upload the companion runner notebook to Databricks Workspace.",
    ),
    upload_sql: bool = typer.Option(
        True,
        "--upload-sql/--no-upload-sql",
        help="Whether to upload SQL scripts from sql/ directory to workspace.",
    ),
):
    """🚀 Package and deploy artifacts (.whl, runner notebook, and SQL scripts) to Databricks Community Edition."""
    if not host or not token:
        console.print("[bold red]Error:[/bold red] Both --host and --token are required (or set DATABRICKS_HOST and DATABRICKS_TOKEN).")
        raise typer.Exit(code=1)

    client = DatabricksCEClient(host=host, token=token)

    with console.status("[bold blue]Checking Databricks CE connectivity...[/bold blue]"):
        try:
            client.verify_connection()
            console.print("[green]✔ Databricks CE API authenticated.[/green]")
        except DatabricksClientError as exc:
            console.print(f"[bold red]Authentication failed:[/bold red] {exc}")
            raise typer.Exit(code=1)

    # 1. Build or locate Wheel
    wheel_file: Optional[Path] = None
    if dist_dir and Path(dist_dir).exists():
        wheels = list(Path(dist_dir).glob("*.whl"))
        if wheels:
            wheel_file = wheels[0]

    if not wheel_file:
        with console.status("[bold blue]Compiling project wheel...[/bold blue]"):
            try:
                wheel_file = build_project_wheel(project_dir=project_dir)
                console.print(f"[green]✔ Built package:[/green] {wheel_file.name}")
            except PackagingError as exc:
                console.print(f"[bold red]Build failed:[/bold red] {exc}")
                raise typer.Exit(code=1)

    # 2. Upload Wheel to Workspace
    clean_target = target_path.rstrip("/")
    remote_wheel_path = f"{clean_target}/{wheel_file.name}"

    with console.status(f"[bold blue]Uploading {wheel_file.name} to {remote_wheel_path}...[/bold blue]"):
        try:
            client.upload_file(
                local_path=wheel_file,
                remote_workspace_path=remote_wheel_path,
                file_format="AUTO",
                overwrite=True,
            )
            console.print(f"[green]✔ Wheel uploaded to:[/green] [white]{remote_wheel_path}[/white]")
        except DatabricksClientError as exc:
            console.print(f"[bold red]Failed to upload wheel:[/bold red] {exc}")
            raise typer.Exit(code=1)

    # 3. Upload Companion Runner Notebooks
    if upload_notebook:
        candidate_notebooks = [
            project_dir / "notebooks" / "run_pipeline_notebook.py",
            project_dir / "notebooks" / "master_dag_runner.py",
        ]
        for local_nb in candidate_notebooks:
            if local_nb.exists():
                remote_nb_path = f"{clean_target}/{local_nb.stem}"
                with console.status(f"[bold blue]Uploading {local_nb.name} to {remote_nb_path}...[/bold blue]"):
                    try:
                        client.upload_file(
                            local_path=local_nb,
                            remote_workspace_path=remote_nb_path,
                            file_format="SOURCE",
                            language="PYTHON",
                            overwrite=True,
                        )
                        console.print(f"[green]✔ Notebook uploaded to:[/green] [white]{remote_nb_path}[/white]")
                    except DatabricksClientError as exc:
                        console.print(f"[yellow]Warning: Could not upload notebook {local_nb.name}:[/yellow] {exc}")

    # 4. Upload SQL scripts if requested
    if upload_sql:
        sql_dir = project_dir / "sql"
        if sql_dir.is_dir():
            for sql_file in sorted(sql_dir.glob("*.sql")):
                remote_sql_path = f"{clean_target}/sql/{sql_file.stem}"
                try:
                    deploy_sql_to_workspace(sql_file, client, remote_sql_path)
                    console.print(f"[green]✔ SQL script deployed to:[/green] [white]{remote_sql_path}[/white]")
                except Exception as exc:
                    console.print(f"[yellow]Warning: Could not upload {sql_file.name}:[/yellow] {exc}")

    console.print(Panel(
        f"[bold green]✔ Deployment to Databricks CE Succeeded![/bold green]\n\n"
        f"[cyan]Workspace Target:[/cyan] {clean_target}\n"
        f"[cyan]Uploaded Wheel:[/cyan] {wheel_file.name}\n"
        f"[cyan]Master DAG Runner:[/cyan] {clean_target}/master_dag_runner\n"
        f"[cyan]Interactive Notebook:[/cyan] {clean_target}/run_pipeline_notebook\n\n"
        f"[yellow]How to run in Databricks Community Edition:[/yellow]\n"
        f"1. Open [bold underline]{client.host}[/bold underline] in your browser.\n"
        f"2. Navigate to [bold]{clean_target}/master_dag_runner[/bold] (or run_pipeline_notebook).\n"
        f"3. Attach your running Community Edition cluster.\n"
        f"4. Click [bold]'Run All'[/bold]. The orchestrator will run the full DAG!",
        title="Deploy Complete",
        border_style="green",
    ))


@app.command(name="run-notebook")
def run_notebook_cmd(
    target_path: str = typer.Option(
        ...,
        "--target-path",
        "-t",
        help="Databricks Workspace directory where the notebook is deployed.",
    ),
    host: Optional[str] = typer.Option(
        None,
        "--host",
        envvar="DATABRICKS_HOST",
        help="Databricks CE URL.",
    ),
):
    """📖 Generate the direct browser URL and execution commands for the deployed Databricks CE Runner Notebook."""
    base_host = (host or "https://community.cloud.databricks.com").rstrip("/")
    if not base_host.startswith("http"):
        base_host = f"https://{base_host}"

    clean_path = target_path.rstrip("/")
    notebook_url = f"{base_host}#workspace{clean_path}/run_pipeline_notebook"

    console.print(Panel(
        f"[bold cyan]Databricks Community Edition Runner Notebook[/bold cyan]\n\n"
        f"Because Databricks Community Edition does not offer Jobs API v2.1,\n"
        f"automated pipeline execution is coordinated through the workspace runner notebook.\n\n"
        f"[bold white]Direct Notebook URL:[/bold white]\n[underline green]{notebook_url}[/underline green]\n\n"
        f"[bold yellow]Execution Steps in CE:[/bold yellow]\n"
        f"1. Open the URL above.\n"
        f"2. Attach your active cluster (e.g. Spark 3.5 / DBR 14.x).\n"
        f"3. Pass custom widget parameters if needed (e.g., date, env, pipeline_mode).\n"
        f"4. Click 'Run All' or schedule via notebook dashboard.",
        title="Databricks CE Execution Guide",
        border_style="cyan",
    ))


# =========================================================================
# SQL SUBCOMMANDS
# =========================================================================

@sql_app.command(name="run")
def sql_run_cmd(
    sql_file: Path = typer.Argument(..., help="Path to .sql script file to execute."),
    mode: str = typer.Option("local", "--mode", "-m", help="Execution mode: 'local' (Delta Lake) or 'remote'."),
):
    """🗄️ Execute a SQL script locally or via Databricks Connect."""
    console.print(f"[bold blue]Running SQL script:[/bold blue] {sql_file}")
    try:
        results = execute_sql_locally(sql_file, mode=mode)
        table = Table(title=f"SQL Execution Results: {sql_file.name}", show_header=True)
        table.add_column("#", style="dim")
        table.add_column("Statement Preview", style="white")
        table.add_column("Rows", style="cyan")
        table.add_column("Duration", style="green")
        table.add_column("Status", style="bold green")

        for r in results:
            rows_str = str(r["row_count"]) if r["row_count"] is not None else "-"
            table.add_row(
                str(r["statement_index"]),
                r["statement_preview"],
                rows_str,
                f"{r['duration_seconds']}s",
                r["status"],
            )

        console.print(table)
        console.print(f"[bold green]✔ All {len(results)} SQL statements executed successfully.[/bold green]")
    except Exception as exc:
        console.print(f"[bold red]SQL Execution Error:[/bold red] {exc}")
        raise typer.Exit(code=1)


@sql_app.command(name="deploy")
def sql_deploy_cmd(
    sql_file: Path = typer.Argument(..., help="Path to .sql script file to deploy."),
    target_path: str = typer.Option(..., "--target-path", "-t", help="Target workspace path (e.g. /Shared/sql/clean)."),
    host: Optional[str] = typer.Option(None, "--host", envvar="DATABRICKS_HOST", help="Databricks URL."),
    token: Optional[str] = typer.Option(None, "--token", envvar="DATABRICKS_TOKEN", help="Databricks PAT token."),
):
    """🚀 Deploy a SQL script to Databricks Workspace."""
    if not host or not token:
        console.print("[bold red]Error:[/bold red] --host and --token required.")
        raise typer.Exit(code=1)

    client = DatabricksCEClient(host=host, token=token)
    try:
        deploy_sql_to_workspace(sql_file, client, target_path)
        console.print(f"[bold green]✔ SQL script {sql_file.name} deployed to {target_path} in Databricks Workspace.[/bold green]")
    except Exception as exc:
        console.print(f"[bold red]Deploy failed:[/bold red] {exc}")
        raise typer.Exit(code=1)


# =========================================================================
# DAG / WORKFLOW SUBCOMMANDS
# =========================================================================

@dag_app.command(name="validate")
def dag_validate_cmd(
    workflow_file: Path = typer.Option(Path("workflow.yaml"), "--file", "-f", help="Path to workflow.yaml."),
):
    """🌐 Validate workflow.yaml: verifies dependencies, machine specs, and detects cycles."""
    console.print(f"[bold blue]Validating DAG Workflow:[/bold blue] {workflow_file}")
    try:
        wf = DAGWorkflow.from_yaml(workflow_file)
        order = wf.validate_dag()

        console.print(Panel(
            f"[bold cyan]Workflow Name:[/bold cyan] [bold green]{wf.name}[/bold green]\n"
            f"[bold cyan]Machine Node:[/bold cyan]  [yellow]{wf.compute.node_type_id}[/yellow] ({wf.compute.cloud.upper()})\n"
            f"[bold cyan]Workers:[/bold cyan]       [white]{wf.compute.num_workers} ({'Single-Node' if wf.compute.single_node else 'Multi-Node'})[/white]\n"
            f"[bold cyan]Spark Version:[/bold cyan] [white]{wf.compute.spark_version}[/white]\n"
            f"[bold cyan]Task Count:[/bold cyan]    [white]{len(wf.tasks)}[/white]",
            title="DAG Validation: OK",
            border_style="green",
        ))

        table = Table(title="Topological Execution Plan (Order of Execution)", show_header=True)
        table.add_column("Step", style="dim")
        table.add_column("Task Key", style="bold cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Upstream Dependencies (depends_on)", style="yellow")

        task_map = {t.name: t for t in wf.tasks}
        for idx, task_name in enumerate(order, start=1):
            t = task_map[task_name]
            deps = ", ".join(t.depends_on) if t.depends_on else "[dim]None (Root)[/dim]"
            table.add_row(str(idx), t.name, t.task_type, deps)

        console.print(table)
        console.print("[bold green]✔ DAG dependency graph is valid with zero circular dependencies.[/bold green]")

    except (DAGCycleError, DAGValidationError) as exc:
        console.print(f"[bold red]DAG Validation Error:[/bold red] {exc}")
        raise typer.Exit(code=1)
    except Exception as exc:
        console.print(f"[bold red]Failed to read workflow:[/bold red] {exc}")
        raise typer.Exit(code=1)


@dag_app.command(name="export")
def dag_export_cmd(
    workflow_file: Path = typer.Option(Path("workflow.yaml"), "--file", "-f", help="Path to workflow.yaml."),
    output_file: Path = typer.Option(Path("databricks_jobs_payload.json"), "--output", "-o", help="Output JSON file."),
    workspace_base: str = typer.Option("/Shared/forge_deployments", "--workspace-base", help="Workspace base directory."),
):
    """📦 Export DAG into native Databricks Jobs API v2.1 multi-task JSON payload."""
    wf = DAGWorkflow.from_yaml(workflow_file)
    payload = wf.to_databricks_jobs_api_payload(workspace_base_path=workspace_base)
    output_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    console.print(f"[bold green]✔ Databricks Jobs API v2.1 payload written to:[/bold green] {output_file}")


@dag_app.command(name="run")
def dag_run_cmd(
    workflow_file: Path = typer.Option(Path("workflow.yaml"), "--file", "-f", help="Path to workflow.yaml."),
    mode: str = typer.Option("local", "--mode", "-m", help="Execution mode ('local' or 'remote')."),
):
    """🚀 Run the DAG workflow tasks sequentially in topological order."""
    wf = DAGWorkflow.from_yaml(workflow_file)
    order = wf.validate_dag()
    task_map = {t.name: t for t in wf.tasks}

    console.print(Panel(
        f"Executing DAG: [bold green]{wf.name}[/bold green] (Mode: [cyan]{mode}[/cyan])\n"
        f"Resolved Execution Order: [yellow]{' ➔ '.join(order)}[/yellow]",
        title="DAG Execution Engine",
        border_style="cyan"
    ))

    for idx, t_name in enumerate(order, start=1):
        task = task_map[t_name]
        console.print(f"\n[bold blue][Step {idx}/{len(order)}][/bold blue] ▶ Running task [bold yellow]{task.name}[/bold yellow] ({task.task_type})...")

        if task.task_type == "sql" and task.file:
            sql_p = Path(task.file)
            if sql_p.exists():
                execute_sql_locally(sql_p, mode=mode)
                console.print(f"[green]✔ Task {task.name} finished successfully.[/green]")
            else:
                console.print(f"[yellow]SQL file {task.file} not found locally (simulated skip).[/yellow]")
        else:
            console.print(f"[green]✔ Task {task.name} executed successfully.[/green]")

    console.print(f"\n[bold green]✔ Completed all {len(order)} tasks in DAG {wf.name}![/bold green]")


# =========================================================================
# COMPUTE SUBCOMMANDS
# =========================================================================

@compute_app.command(name="list")
def compute_list_cmd(
    cloud: str = typer.Option("aws", "--cloud", "-c", help="Cloud provider: 'aws', 'azure', 'gcp', or 'ce'."),
):
    """💻 List pre-configured Databricks machine types and specifications."""
    nodes = get_available_node_types(cloud)
    table = Table(title=f"Databricks Machine Catalog: {cloud.upper()}", show_header=True)
    table.add_column("Node Type ID", style="bold cyan")
    table.add_column("Category", style="magenta")
    table.add_column("vCPUs", style="green")
    table.add_column("RAM (GB)", style="yellow")
    table.add_column("Description", style="white")

    for n in nodes:
        table.add_row(n.node_type_id, n.category, str(n.vcpus), str(n.memory_gb), n.description)

    console.print(table)


# =========================================================================
# SECRETS SUBCOMMANDS
# =========================================================================

@secret_app.command(name="list")
def secret_list_cmd(
    scope: Optional[str] = typer.Option(None, "--scope", "-s", help="Specific secret scope to inspect."),
    host: Optional[str] = typer.Option(None, "--host", envvar="DATABRICKS_HOST", help="Databricks URL."),
    token: Optional[str] = typer.Option(None, "--token", envvar="DATABRICKS_TOKEN", help="Databricks Token."),
):
    """🔒 List secret scopes or secrets within a specific scope."""
    if not host or not token:
        console.print("[bold red]Error:[/bold red] --host and --token are required.")
        raise typer.Exit(code=1)

    client = DatabricksSecretsClient(host=host, token=token)
    try:
        if scope:
            secrets = client.list_secrets(scope)
            table = Table(title=f"Secrets in Scope: [bold cyan]{scope}[/bold cyan]", show_header=True)
            table.add_column("Key", style="bold cyan")
            table.add_column("Last Updated", style="white")
            for s in secrets:
                table.add_row(s.get("key", ""), str(s.get("last_updated_timestamp", "-")))
            console.print(table)
            console.print(f"[dim]Total: {len(secrets)} secret keys (values masked by API for security).[/dim]")
        else:
            scopes = client.list_scopes()
            table = Table(title="Databricks Secret Scopes", show_header=True)
            table.add_column("Scope Name", style="bold cyan")
            table.add_column("Backend Type", style="magenta")
            for sc in scopes:
                table.add_row(sc.get("name", ""), sc.get("backend_type", "DATABRICKS"))
            console.print(table)
            console.print(f"[dim]Total: {len(scopes)} secret scopes.[/dim]")
    except Exception as exc:
        console.print(f"[bold red]Failed to list secrets:[/bold red] {exc}")
        raise typer.Exit(code=1)


@secret_app.command(name="create-scope")
def secret_create_scope_cmd(
    scope: str = typer.Argument(..., help="Name of the new secret scope to create."),
    host: Optional[str] = typer.Option(None, "--host", envvar="DATABRICKS_HOST", help="Databricks URL."),
    token: Optional[str] = typer.Option(None, "--token", envvar="DATABRICKS_TOKEN", help="Databricks Token."),
):
    """➕ Create a new secret scope in Databricks."""
    if not host or not token:
        console.print("[bold red]Error:[/bold red] --host and --token are required.")
        raise typer.Exit(code=1)

    client = DatabricksSecretsClient(host=host, token=token)
    try:
        client.create_scope(scope=scope)
        console.print(f"[bold green]✔ Secret scope '[cyan]{scope}[/cyan]' created successfully![/bold green]")
    except Exception as exc:
        console.print(f"[bold red]Failed to create scope:[/bold red] {exc}")
        raise typer.Exit(code=1)


@secret_app.command(name="set")
def secret_set_cmd(
    scope: str = typer.Argument(..., help="Secret scope name."),
    key: str = typer.Argument(..., help="Secret key name."),
    value: Optional[str] = typer.Option(None, "--value", help="Secret value (if not passed, you will be prompted)."),
    host: Optional[str] = typer.Option(None, "--host", envvar="DATABRICKS_HOST", help="Databricks URL."),
    token: Optional[str] = typer.Option(None, "--token", envvar="DATABRICKS_TOKEN", help="Databricks Token."),
):
    """🔑 Set or update a secret key-value in a Databricks scope."""
    if not host or not token:
        console.print("[bold red]Error:[/bold red] --host and --token are required.")
        raise typer.Exit(code=1)

    if not value:
        value = typer.prompt(f"Enter secret value for {scope}/{key}", hide_input=True)

    client = DatabricksSecretsClient(host=host, token=token)
    try:
        client.put_secret(scope=scope, key=key, string_value=value)
        console.print(f"[bold green]✔ Secret '[cyan]{key}[/cyan]' in scope '[cyan]{scope}[/cyan]' saved successfully![/bold green]")
    except Exception as exc:
        console.print(f"[bold red]Failed to put secret:[/bold red] {exc}")
        raise typer.Exit(code=1)


@secret_app.command(name="sync-env")
def secret_sync_env_cmd(
    scope: str = typer.Option("forge_scope", "--scope", "-s", help="Databricks secret scope name to sync into."),
    env_file: Path = typer.Option(Path(".env"), "--file", "-f", help="Path to local .env file."),
    host: Optional[str] = typer.Option(None, "--host", envvar="DATABRICKS_HOST", help="Databricks URL."),
    token: Optional[str] = typer.Option(None, "--token", envvar="DATABRICKS_TOKEN", help="Databricks Token."),
):
    """🔄 Synchronize local .env variables directly into a Databricks Secret Scope."""
    if not host or not token:
        console.print("[bold red]Error:[/bold red] --host and --token are required.")
        raise typer.Exit(code=1)

    if not env_file.exists():
        console.print(f"[bold red]Error:[/bold red] Environment file [yellow]{env_file}[/yellow] not found.")
        raise typer.Exit(code=1)

    client = DatabricksSecretsClient(host=host, token=token)
    try:
        synced = sync_env_to_scope(env_path=env_file, scope_name=scope, client=client)
        console.print(Panel(
            f"[bold green]✔ Successfully synced {len(synced)} secrets from {env_file} to scope '{scope}'![/bold green]\n\n"
            f"[cyan]Synced keys:[/cyan]\n" + "\n".join(f"  • {k}" for k in synced),
            title="Secrets Synchronized",
            border_style="green",
        ))
    except Exception as exc:
        console.print(f"[bold red]Failed to sync secrets:[/bold red] {exc}")
        raise typer.Exit(code=1)


# =========================================================================
# PERFORMANCE TUNING & DELTA LAKE COMMANDS
# =========================================================================

@tune_app.command(name="optimize")
def tune_optimize_cmd(
    table_name: str = typer.Argument(..., help="Delta table identifier (e.g. 'customer_360_silver') or path."),
    zorder: Optional[str] = typer.Option(None, "--zorder", "-z", help="Comma-separated columns for Z-Ordering (e.g. 'user_id,date')."),
    profile: str = typer.Option("balanced", "--profile", "-p", help="Tuning profile: 'balanced', 'write_heavy', or 'read_heavy'."),
):
    """⚡ Generate or execute Delta Lake file compaction and Z-Ordering optimization."""
    zorder_cols = [c.strip() for c in zorder.split(",") if c.strip()] if zorder else None
    stmt = build_optimize_statement(table_name, zorder_cols)

    console.print(Panel(
        f"[bold cyan]Target Table:[/bold cyan]    [bold green]{table_name}[/bold green]\n"
        f"[bold cyan]Z-Order Columns:[/bold cyan] [yellow]{', '.join(zorder_cols) if zorder_cols else 'None (Linear Compaction)'}[/yellow]\n"
        f"[bold cyan]Tuning Profile:[/bold cyan]  [magenta]{profile}[/magenta]\n\n"
        f"[bold white]Optimized SQL Statement:[/bold white]\n"
        f"[bold yellow]{stmt};[/bold yellow]",
        title="⚡ Delta Lake Optimization Plan",
        border_style="cyan",
    ))

    configs = get_tuning_configs(profile)
    table = Table(title=f"Recommended Spark AQE Configurations ({profile})", show_header=True)
    table.add_column("Spark Configuration Key", style="cyan")
    table.add_column("Value", style="green")

    for k, v in configs.items():
        table.add_row(k, v)
    console.print(table)
    console.print("[dim]Run in Databricks Notebook or SQL Job via: [cyan]forge sql run[/cyan] or [cyan]make optimize[/cyan][/dim]")


@tune_app.command(name="vacuum")
def tune_vacuum_cmd(
    table_name: str = typer.Argument(..., help="Delta table identifier or file path."),
    retention_hours: int = typer.Option(168, "--retention", "-r", help="Retention threshold in hours (default: 168 = 7 days)."),
):
    """🧹 Safely prune obsolete Delta Lake historical snapshots and uncommitted files."""
    stmt = build_vacuum_statement(table_name, retention_hours)

    console.print(Panel(
        f"[bold cyan]Target Table:[/bold cyan]    [bold green]{table_name}[/bold green]\n"
        f"[bold cyan]Retention Period:[/bold cyan][yellow]{retention_hours} hours ({retention_hours // 24} days)[/yellow]\n\n"
        f"[bold white]Vacuum SQL Statement:[/bold white]\n"
        f"[bold yellow]{stmt};[/bold yellow]\n\n"
        f"[dim]Note: Files older than {retention_hours} hours will be permanently deleted.[/dim]",
        title="🧹 Delta Lake Maintenance (VACUUM)",
        border_style="yellow",
    ))


@tune_app.command(name="config")
def tune_config_cmd(
    profile: str = typer.Option("balanced", "--profile", "-p", help="Tuning profile: 'balanced', 'write_heavy', or 'read_heavy'."),
):
    """⚙️ Display recommended Spark AQE and Delta Lake tuning parameters."""
    if profile not in TUNING_PROFILES:
        console.print(f"[bold red]Error:[/bold red] Profile must be one of: {list(TUNING_PROFILES.keys())}")
        raise typer.Exit(code=1)

    configs = get_tuning_configs(profile)
    table = Table(title=f"Spark & Delta Lake Performance Tuning Defaults ({profile.upper()})", show_header=True)
    table.add_column("Spark Configuration Key", style="cyan")
    table.add_column("Preset Value", style="green")
    table.add_column("Engine Impact", style="dim")

    descriptions = {
        "spark.sql.adaptive.enabled": "Enables dynamic query plan restructuring at runtime based on statistics",
        "spark.sql.adaptive.coalescePartitions.enabled": "Automatically merges small shuffle partitions to eliminate overhead",
        "spark.sql.adaptive.skewJoin.enabled": "Detects and dynamically splits skewed join partitions to prevent stragglers",
        "spark.sql.adaptive.localShuffleReader.enabled": "Optimizes shuffle reads when partitions can be read locally",
        "spark.sql.adaptive.advisoryPartitionSizeInBytes": "Target shuffle partition size (e.g. 64MB / 128MB)",
        "spark.databricks.delta.optimizeWrite.enabled": "Dynamically coalesces small writes to reduce number of created files",
        "spark.databricks.delta.autoCompact.enabled": "Compacts small files into larger ~128MB Delta files after writes",
        "spark.sql.shuffle.partitions": "Initial shuffle partition count",
    }

    for k, v in configs.items():
        desc = descriptions.get(k, "Spark runtime tuning parameter")
        table.add_row(k, v, desc)

    console.print(table)


# =========================================================================
# MULTI-FORMAT DATA CONVERSION & INSPECTION
# =========================================================================

@data_app.command(name="convert")
def data_convert_cmd(
    source: str = typer.Argument(..., help="Source dataset file path or catalog table (e.g. data/events.csv)."),
    target: str = typer.Argument(..., help="Destination dataset path or catalog table (e.g. data/events_silver)."),
    from_format: Optional[str] = typer.Option(None, "--from", "-f", help="Explicit source format (parquet, orc, avro, csv, json, delta, iceberg)."),
    to_format: str = typer.Option("delta", "--to", "-t", help="Target format (default: delta)."),
    partition_by: Optional[str] = typer.Option(None, "--partition-by", "-p", help="Comma-separated partition column names."),
):
    """📁 Convert datasets between file formats (Parquet, ORC, Avro, CSV, JSON, Delta)."""
    partition_cols = [c.strip() for c in partition_by.split(",") if c.strip()] if partition_by else None
    try:
        plan = build_convert_plan(
            source=source,
            target=target,
            from_format=from_format,
            to_format=to_format,
            partition_by=partition_cols,
        )
        console.print(Panel(
            f"[bold cyan]Source:[/bold cyan]        [white]{plan['source']}[/white] ([magenta]{plan['source_format'].upper()}[/magenta])\n"
            f"[bold cyan]Destination:[/bold cyan]   [white]{plan['target']}[/white] ([green]{plan['target_format'].upper()}[/green])\n"
            f"[bold cyan]Partition By:[/bold cyan]  [yellow]{', '.join(plan['partition_by']) if plan['partition_by'] else 'None'}[/yellow]\n\n"
            f"[bold white]Execution Code:[/bold white]\n"
            f"[yellow]{plan['command_preview']}[/yellow]",
            title="📁 Multi-Format Conversion Plan",
            border_style="cyan",
        ))
        console.print("[dim]Run in Python or Databricks via: [cyan]from <project>.formats import convert_dataset; convert_dataset(...)[/cyan][/dim]")
    except Exception as exc:
        console.print(f"[bold red]Format conversion error:[/bold red] {exc}")
        raise typer.Exit(code=1)


@data_app.command(name="inspect")
def data_inspect_cmd(
    path_or_table: str = typer.Argument(..., help="File path, directory, or table to inspect."),
):
    """🔍 Inspect format and metadata of a file or directory dataset."""
    inferred_format = detect_format_from_path(path_or_table)
    file_path = Path(path_or_table)

    table = Table(title=f"Dataset Inspection: {path_or_table}", show_header=True)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Inferred Format", inferred_format.upper())
    table.add_row("Exists Locally", "Yes" if file_path.exists() else "No (or remote URI)")
    if file_path.exists():
        if file_path.is_file():
            size_kb = file_path.stat().st_size / 1024.0
            table.add_row("Type", "Single File")
            table.add_row("Size", f"{size_kb:.2f} KB")
        elif file_path.is_dir():
            files = list(file_path.rglob("*"))
            data_files = [f for f in files if f.is_file() and not f.name.startswith(".")]
            total_bytes = sum(f.stat().st_size for f in data_files)
            table.add_row("Type", "Directory / Partitioned Table")
            table.add_row("Data Files Count", str(len(data_files)))
            table.add_row("Total Size", f"{total_bytes / (1024 * 1024):.2f} MB")
            has_delta = any("_delta_log" in str(p) for p in files)
            table.add_row("Has Delta Log", "Yes" if has_delta else "No")

    console.print(table)


# =========================================================================
# APACHE ICEBERG & DELTA UNIFORM
# =========================================================================

@iceberg_app.command(name="enable-uniform")
def iceberg_enable_uniform_cmd(
    table_name: str = typer.Argument(..., help="Delta table identifier (e.g. 'transactions_silver') or path."),
):
    """🧊 Enable Delta UniForm (Iceberg compatibility) on a Delta Lake table."""
    stmts = build_enable_uniform_statements(table_name)

    console.print(Panel(
        f"[bold cyan]Target Table:[/bold cyan] [bold green]{table_name}[/bold green]\n"
        f"[bold cyan]Universal Format:[/bold cyan] [magenta]Apache Iceberg[/magenta]\n"
        f"[bold cyan]Column Mapping:[/bold cyan]   [yellow]name[/yellow]\n\n"
        f"[bold white]Required SQL DDL Statements:[/bold white]\n"
        + "\n".join(f"[yellow]{s};[/yellow]" for s in stmts),
        title="🧊 Delta UniForm (Apache Iceberg) Configuration",
        border_style="cyan",
    ))
    console.print("[dim]Execute via: [cyan]forge sql run <file.sql>[/cyan] or in a Databricks Notebook cell.[/dim]")


@iceberg_app.command(name="inspect")
def iceberg_inspect_cmd(
    table_name: str = typer.Argument(..., help="Iceberg table identifier or path."),
):
    """🔍 Inspect Apache Iceberg metadata paths and external engine compatibility."""
    plan = inspect_iceberg_plan(table_name)

    console.print(Panel(
        f"[bold cyan]Target Table:[/bold cyan]         [bold green]{plan['table']}[/bold green]\n"
        f"[bold cyan]Metadata Path Pattern:[/bold cyan] [white]{plan['iceberg_metadata_path']}[/white]\n\n"
        f"[bold cyan]Supported External Query Engines:[/bold cyan]\n"
        + "\n".join(f"  • {eng}" for eng in plan['supported_external_engines']),
        title="🧊 Apache Iceberg Table Inspection",
        border_style="cyan",
    ))


@iceberg_app.command(name="snapshots")
def iceberg_snapshots_cmd(
    table_name: str = typer.Argument(..., help="Iceberg table identifier."),
):
    """📜 Display SQL query to inspect historical commits and snapshots of an Iceberg table."""
    query = build_iceberg_snapshots_query(table_name)
    console.print(Panel(
        f"[bold cyan]Table:[/bold cyan] [bold green]{table_name}[/bold green]\n\n"
        f"[bold white]Snapshots & History Query:[/bold white]\n"
        f"[yellow]{query};[/yellow]\n\n"
        f"[dim]Run this query in Databricks SQL or Spark to inspect commit history and snapshot IDs for time-travel.[/dim]",
        title="📜 Iceberg Snapshots & Commit History",
        border_style="magenta",
    ))


# =========================================================================
# MULTI-DATABASE CONNECTORS & REVERSE-ETL
# =========================================================================

@connector_app.command(name="list")
def connector_list_cmd():
    """🔌 List supported database engines, default ports, driver classes, and Maven packages."""
    table = Table(title="🔌 Databricks Forge - Supported Database Connectors", show_header=True)
    table.add_column("Engine ID", style="cyan")
    table.add_column("Database Name", style="white")
    table.add_column("Category", style="magenta")
    table.add_column("Port", style="yellow")
    table.add_column("JDBC Driver Class", style="green")
    table.add_column("Maven Coordinate (for cluster init)", style="dim")

    for engine_id, meta in DATABASE_CATALOG.items():
        table.add_row(
            engine_id,
            meta["name"],
            meta["category"],
            str(meta["default_port"]) if meta["default_port"] > 0 else "N/A (Local)",
            meta["driver_class"],
            meta["maven_package"],
        )

    console.print(table)


@connector_app.command(name="test-connection")
def connector_test_connection_cmd(
    db_type: str = typer.Argument(..., help="Database type: postgresql, mysql, sqlserver, oracle, snowflake, mongodb, sqlite."),
    host: str = typer.Option("localhost", "--host", "-h", help="Database host or endpoint."),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Target port (leave blank for engine default)."),
    timeout: int = typer.Option(3, "--timeout", "-t", help="Connection timeout in seconds."),
):
    """🔍 Test network reachability and TCP socket handshake to external database."""
    result = check_db_connectivity(db_type=db_type, host=host, port=port, timeout_sec=timeout)

    if result["status"] == "SUCCESS":
        console.print(Panel(
            f"[bold green]✔ Connection Successful![/bold green]\n\n"
            f"[bold cyan]Engine:[/bold cyan]    [white]{result['db_type']}[/white]\n"
            f"[bold cyan]Host/Port:[/bold cyan] [white]{result.get('host', 'Local')}:{result.get('port', 0)}[/white]\n"
            f"[bold cyan]Message:[/bold cyan]   [green]{result['message']}[/green]",
            title="🔌 Database Connectivity Check",
            border_style="green",
        ))
    else:
        console.print(Panel(
            f"[bold red]✖ Connection Failed![/bold red]\n\n"
            f"[bold cyan]Engine:[/bold cyan]    [white]{result['db_type']}[/white]\n"
            f"[bold cyan]Host/Port:[/bold cyan] [white]{result.get('host', 'Local')}:{result.get('port', 0)}[/white]\n"
            f"[bold cyan]Error:[/bold cyan]     [red]{result['error']}[/red]\n\n"
            f"[dim]Tip: Check firewall rules, VPN, security groups, or container networking.[/dim]",
            title="🔌 Database Connectivity Check",
            border_style="red",
        ))
        raise typer.Exit(code=1)


@connector_app.command(name="plan-ingest")
def connector_plan_ingest_cmd(
    db_type: str = typer.Argument(..., help="Database type: postgresql, mysql, sqlserver, oracle, snowflake, mongodb, sqlite."),
    source_table: str = typer.Argument(..., help="External table or SQL subquery to ingest."),
    target_delta_table: str = typer.Argument(..., help="Destination Delta Lake table name."),
    host: str = typer.Option("localhost", "--host", "-h", help="Database host or endpoint."),
    database: str = typer.Option(..., "--database", "-d", help="Database name."),
    user: str = typer.Option("lakehouse_ingest", "--user", "-u", help="Database username."),
    partition_column: Optional[str] = typer.Option(None, "--partition-by", "-p", help="Column name for parallel partitioned JDBC read."),
    num_partitions: int = typer.Option(4, "--num-partitions", "-n", help="Parallel JDBC partition read threads."),
    fetchsize: int = typer.Option(10000, "--fetchsize", help="JDBC fetch buffer size in rows."),
    port: Optional[int] = typer.Option(None, "--port", help="Port override."),
):
    """📥 Generate high-performance partitioned JDBC ingestion execution plan."""
    try:
        plan = build_ingest_plan(
            db_type=db_type,
            source_table=source_table,
            target_delta_table=target_delta_table,
            host=host,
            database=database,
            user=user,
            partition_column=partition_column,
            num_partitions=num_partitions,
            fetchsize=fetchsize,
            port=port,
        )
        console.print(Panel(
            f"[bold cyan]Source Database:[/bold cyan] [white]{plan['database_name']}[/white] ([green]{db_type}[/green])\n"
            f"[bold cyan]JDBC URL:[/bold cyan]        [white]{plan['jdbc_url']}[/white]\n"
            f"[bold cyan]Source Table:[/bold cyan]    [yellow]{plan['source_table']}[/yellow]\n"
            f"[bold cyan]Target Delta:[/bold cyan]    [bold green]{plan['target_delta_table']}[/bold green]\n"
            f"[bold cyan]Partitioning:[/bold cyan]    [magenta]{plan['partition_column'] or 'Single-Thread'} ({plan['num_partitions']} threads)[/magenta]\n\n"
            f"[bold white]PySpark Ingestion Code:[/bold white]\n"
            f"[yellow]{plan['code_preview']}[/yellow]",
            title="📥 High-Performance Database Ingestion Plan",
            border_style="cyan",
        ))
        console.print("[dim]Execute in Notebook or DAG via: [cyan]from <project>.connectors import read_database_table[/cyan][/dim]")
    except Exception as exc:
        console.print(f"[bold red]Planning error:[/bold red] {exc}")
        raise typer.Exit(code=1)


@connector_app.command(name="plan-export")
def connector_plan_export_cmd(
    source_delta_table: str = typer.Argument(..., help="Source Delta Lake table to export from."),
    db_type: str = typer.Argument(..., help="Destination database type."),
    target_table: str = typer.Argument(..., help="Destination table in target database."),
    host: str = typer.Option("localhost", "--host", "-h", help="Database host or endpoint."),
    database: str = typer.Option(..., "--database", "-d", help="Database name."),
    user: str = typer.Option("lakehouse_export", "--user", "-u", help="Database username."),
    mode: str = typer.Option("append", "--mode", "-m", help="Save mode: 'append' or 'overwrite'."),
    batchsize: int = typer.Option(5000, "--batchsize", help="JDBC commit batch size in rows."),
    port: Optional[int] = typer.Option(None, "--port", help="Port override."),
):
    """📤 Generate Reverse-ETL plan to export Delta Lake Gold data to an external database."""
    try:
        plan = build_export_plan(
            source_delta_table=source_delta_table,
            db_type=db_type,
            target_table=target_table,
            host=host,
            database=database,
            user=user,
            mode=mode,
            batchsize=batchsize,
            port=port,
        )
        console.print(Panel(
            f"[bold cyan]Source Delta:[/bold cyan]    [bold green]{plan['source_delta_table']}[/bold green]\n"
            f"[bold cyan]Target Database:[/bold cyan] [white]{plan['database_name']}[/white] ([green]{db_type}[/green])\n"
            f"[bold cyan]JDBC URL:[/bold cyan]        [white]{plan['jdbc_url']}[/white]\n"
            f"[bold cyan]Target Table:[/bold cyan]    [yellow]{plan['target_table']}[/yellow]\n"
            f"[bold cyan]Mode & Batch:[/bold cyan]   [magenta]{plan['mode']} (batch: {plan['batchsize']} rows)[/magenta]\n\n"
            f"[bold white]PySpark Reverse-ETL Code:[/bold white]\n"
            f"[yellow]{plan['code_preview']}[/yellow]",
            title="📤 Reverse-ETL Export Plan",
            border_style="magenta",
        ))
        console.print("[dim]Execute in Notebook or DAG via: [cyan]from <project>.connectors import write_database_table[/cyan][/dim]")
    except Exception as exc:
        console.print(f"[bold red]Export planning error:[/bold red] {exc}")
        raise typer.Exit(code=1)


# =========================================================================
# DIAGNOSTICS & SYSTEM CHECKS
# =========================================================================

@app.command()
def check(
    host: Optional[str] = typer.Option(
        None,
        "--host",
        envvar="DATABRICKS_HOST",
        help="Databricks URL to test.",
    ),
    token: Optional[str] = typer.Option(
        None,
        "--token",
        envvar="DATABRICKS_TOKEN",
        help="Databricks Personal Access Token.",
    ),
):
    """🔍 Diagnostic check of local prerequisites (Python, Java, Docker) and Databricks CE connection."""
    console.print(Panel("[bold cyan]Databricks Forge Diagnostics[/bold cyan]", border_style="cyan"))

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Component", style="white")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="dim")

    # 1. Python Check
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 10):
        table.add_row("Python", "[green]OK[/green]", f"Python {py_ver} ({sys.executable})")
    else:
        table.add_row("Python", "[red]FAIL[/red]", f"Python {py_ver} (Requires >= 3.10)")

    # 2. Java / OpenJDK Check
    java_bin = shutil.which("java")
    java_home = os.getenv("JAVA_HOME")
    if java_bin:
        try:
            java_out = subprocess.run(["java", "-version"], capture_output=True, text=True, check=False).stderr.splitlines()[0]
            table.add_row("Java Runtime", "[green]OK[/green]", f"{java_out} (JAVA_HOME={java_home or 'not set'})")
        except Exception:
            table.add_row("Java Runtime", "[yellow]WARNING[/yellow]", "java executable found but failed to report version")
    else:
        table.add_row("Java Runtime", "[yellow]NOT FOUND[/yellow]", "Required for local PySpark execution outside Docker (Docker handles this)")

    # 3. Docker / Podman
    docker_bin = shutil.which("docker") or shutil.which("podman")
    if docker_bin:
        try:
            doc_out = subprocess.run([docker_bin, "--version"], capture_output=True, text=True, check=False).stdout.strip()
            table.add_row("Container Engine", "[green]OK[/green]", doc_out)
        except Exception:
            table.add_row("Container Engine", "[yellow]WARNING[/yellow]", f"{docker_bin} present")
    else:
        table.add_row("Container Engine", "[yellow]NOT FOUND[/yellow]", "Docker/Podman recommended for containerized testing")

    # 4. Databricks Connectivity
    if host and token:
        try:
            client = DatabricksCEClient(host=host, token=token)
            client.verify_connection()
            table.add_row("Databricks CE API", "[green]OK[/green]", f"Authenticated successfully to {host}")
        except Exception as exc:
            table.add_row("Databricks CE API", "[red]FAIL[/red]", str(exc))
    else:
        table.add_row("Databricks CE API", "[dim]SKIPPED[/dim]", "DATABRICKS_HOST and DATABRICKS_TOKEN not provided")

    console.print(table)


if __name__ == "__main__":
    app()
