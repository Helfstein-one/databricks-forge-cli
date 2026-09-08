"""Project scaffolding generator using Jinja2 templates."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
import jinja2


def slugify(name: str) -> str:
    """Converts a project name to a valid Python package identifier (slug)."""
    clean = re.sub(r"[^\w\s-]", "", name).strip().lower()
    slug = re.sub(r"[-\s]+", "_", clean)
    if not slug or slug[0].isdigit():
        slug = f"proj_{slug}"
    return slug


def get_git_config_user() -> Dict[str, str]:
    """Retrieves user.name and user.email from local git config if available."""
    name = "Databricks Engineer"
    email = "engineer@example.com"
    try:
        n = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            check=False
        ).stdout.strip()
        if n:
            name = n
        e = subprocess.run(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            check=False
        ).stdout.strip()
        if e:
            email = e
    except Exception:
        pass
    return {"name": name, "email": email}


class ProjectGenerator:
    """Renders the base_project template into a target directory."""

    def __init__(self, templates_dir: Optional[Path] = None):
        if templates_dir is None:
            self.templates_dir = Path(__file__).parent.parent / "templates" / "base_project"
        else:
            self.templates_dir = Path(templates_dir)

        if not self.templates_dir.exists():
            raise FileNotFoundError(f"Templates directory not found: {self.templates_dir}")

        self.jinja_env = jinja2.Environment(
            undefined=jinja2.StrictUndefined,
            keep_trailing_newline=True,
        )

    def create(
        self,
        project_name: str,
        target_dir: Path | str,
        description: Optional[str] = None,
        author_name: Optional[str] = None,
        author_email: Optional[str] = None,
        pyspark_version: str = "3.5.0",
        delta_version: str = "3.0.0",
        python_version: str = "3.11",
        cloud: str = "ce",
        node_type_id: Optional[str] = None,
        num_workers: int = 0,
        spark_version: str = "14.3.x-scala2.12",
    ) -> List[Path]:
        """Creates a new scaffolded Lakehouse project."""
        dest_root = Path(target_dir).resolve()
        dest_root.mkdir(parents=True, exist_ok=True)

        slug = slugify(project_name)
        git_user = get_git_config_user()

        selected_node = node_type_id
        if not selected_node:
            selected_node = "SingleNode" if cloud == "ce" else ("Standard_DS3_v2" if cloud == "azure" else ("n1-standard-4" if cloud == "gcp" else "m5d.large"))

        context: Dict[str, Any] = {
            "project_name": project_name,
            "project_slug": slug,
            "description": description or f"Lakehouse data pipeline powered by Databricks Forge CLI for {project_name}",
            "author_name": author_name or git_user["name"],
            "author_email": author_email or git_user["email"],
            "pyspark_version": pyspark_version,
            "delta_version": delta_version,
            "python_version": python_version,
            "cloud": cloud,
            "node_type_id": selected_node,
            "num_workers": num_workers,
            "single_node": num_workers == 0 or cloud == "ce",
            "spark_version": spark_version,
        }

        generated_files: List[Path] = []

        for root, dirs, files in os.walk(self.templates_dir):
            rel_root = Path(root).relative_to(self.templates_dir)
            
            # Resolve directory substitutions like src/{{project_slug}}
            rel_dir_parts = [part.replace("{{project_slug}}", slug) for part in rel_root.parts]
            target_sub_dir = dest_root.joinpath(*rel_dir_parts)
            target_sub_dir.mkdir(parents=True, exist_ok=True)

            for filename in files:
                src_file = Path(root) / filename
                
                # Determine destination file name
                dest_filename = filename
                if dest_filename.endswith(".jinja"):
                    dest_filename = dest_filename[:-6]
                dest_filename = dest_filename.replace("{{project_slug}}", slug)

                dest_file = target_sub_dir / dest_filename

                # Read and render content
                try:
                    raw_content = src_file.read_text(encoding="utf-8")
                    template = self.jinja_env.from_string(raw_content)
                    rendered_content = template.render(**context)
                    dest_file.write_text(rendered_content, encoding="utf-8")
                except UnicodeDecodeError:
                    # Binary file, copy directly
                    shutil.copy2(src_file, dest_file)

                # Preserve permissions if executable
                if os.access(src_file, os.X_OK):
                    dest_file.chmod(dest_file.stat().st_mode | 0o111)

                generated_files.append(dest_file)

        return generated_files
