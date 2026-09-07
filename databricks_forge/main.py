"""Main CLI Entrypoint for Databricks Forge CLI."""

from __future__ import annotations

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
from databricks_forge.core.generator import ProjectGenerator
from databricks_forge.core.packaging import build_project_wheel, PackagingError

app = typer.Typer(
    name="forge",
    help="⚡ Databricks Forge CLI - Industrial scaffolding, local testing, packaging, and CI/CD for Databricks CE.",
    add_completion=True,
    rich_markup_mode="rich",
)
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
):
    """🚀 Scaffold a production-grade Lakehouse project with Docker, Databricks Connect, Chispa, and GitHub Actions."""
    target_path = output_dir / project_name

    if target_path.exists() and any(target_path.iterdir()):
        console.print(f"[bold red]Error:[/bold red] Target directory [yellow]{target_path}[/yellow] already exists and is not empty.")
        raise typer.Exit(code=1)

    console.print(Panel(
        f"[bold cyan]Databricks Forge Generator[/bold cyan]\n"
        f"Creating Lakehouse project: [bold green]{project_name}[/bold green]\n"
        f"Target location: [bold white]{target_path}[/bold white]",
        title="Forge Scaffolding",
        border_style="cyan"
    ))

    try:
        generator = ProjectGenerator()
        files = generator.create(
            project_name=project_name,
            target_dir=target_path,
            description=description,
            author_name=author,
            author_email=email,
        )

        table = Table(title="Generated Project Artifacts", show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan")
        table.add_column("Key Files / Paths", style="white")

        table.add_row("Core Source", f"src/{generator.jinja_env.from_string('{{project_slug}}').render(project_slug=project_name.lower().replace('-', '_'))}/ (session.py, catalog.py, pipelines, entrypoint.py)")
        table.add_row("Databricks Notebooks", "notebooks/run_pipeline_notebook.py (CE Runner Notebook)")
        table.add_row("Docker Container", "docker/Dockerfile, docker/docker-compose.yml (Java 11 + PySpark 3.5)")
        table.add_row("Test Suite", "tests/unit/ (Chispa), tests/integration/, tests/performance/")
        table.add_row("CI/CD Pipeline", ".github/workflows/ci.yml, .github/workflows/cd.yml")
        table.add_row("Dev Automation", "Makefile, pyproject.toml, config/, .env.example")

        console.print(table)
        console.print(f"\n[bold green]✔ Successfully created {len(files)} files in {target_path}[/bold green]")
        console.print("\n[bold yellow]Next steps:[/bold yellow]")
        console.print(f"  1. [cyan]cd {target_path}[/cyan]")
        console.print("  2. [cyan]cp .env.example .env[/cyan] (fill Databricks credentials if testing Databricks Connect)")
        console.print("  3. [cyan]make docker-test[/cyan] (or [cyan]pytest tests/unit[/cyan] locally)")
        console.print("  4. [cyan]forge build[/cyan] && [cyan]forge deploy[/cyan]")

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
):
    """🚀 Package and deploy artifacts (.whl and runner notebook) to Databricks Community Edition."""
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

    # 3. Upload Companion Runner Notebook if present
    if upload_notebook:
        candidate_notebooks = [
            project_dir / "notebooks" / "run_pipeline_notebook.py",
            project_dir / "run_pipeline_notebook.py",
        ]
        local_nb = next((nb for nb in candidate_notebooks if nb.exists()), None)
        if local_nb:
            remote_nb_path = f"{clean_target}/run_pipeline_notebook"
            with console.status(f"[bold blue]Uploading runner notebook to {remote_nb_path}...[/bold blue]"):
                try:
                    client.upload_file(
                        local_path=local_nb,
                        remote_workspace_path=remote_nb_path,
                        file_format="SOURCE",
                        language="PYTHON",
                        overwrite=True,
                    )
                    console.print(f"[green]✔ Runner notebook uploaded to:[/green] [white]{remote_nb_path}[/white]")
                except DatabricksClientError as exc:
                    console.print(f"[yellow]Warning: Could not upload runner notebook:[/yellow] {exc}")

    console.print(Panel(
        f"[bold green]✔ Deployment to Databricks CE Succeeded![/bold green]\n\n"
        f"[cyan]Workspace Target:[/cyan] {clean_target}\n"
        f"[cyan]Uploaded Wheel:[/cyan] {wheel_file.name}\n"
        f"[cyan]Runner Notebook:[/cyan] {clean_target}/run_pipeline_notebook\n\n"
        f"[yellow]How to run in Databricks Community Edition:[/yellow]\n"
        f"1. Open [bold underline]{client.host}[/bold underline] in your browser.\n"
        f"2. Navigate to [bold]{clean_target}/run_pipeline_notebook[/bold].\n"
        f"3. Attach your running Community Edition cluster.\n"
        f"4. Click [bold]'Run All'[/bold]. The notebook will install the deployed wheel and execute the pipeline!",
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
