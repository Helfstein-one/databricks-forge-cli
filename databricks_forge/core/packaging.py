"""Wheel packaging and build utilities for Databricks Forge projects."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


class PackagingError(Exception):
    """Raised when building package fails."""
    pass


def find_project_root(start_path: Optional[Path] = None) -> Path:
    """Find the root of a project containing pyproject.toml."""
    current = Path(start_path or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return current


def clean_dist(dist_dir: Path) -> None:
    """Removes previous wheel artifacts in dist directory."""
    if dist_dir.exists():
        for item in dist_dir.glob("*.whl"):
            try:
                item.unlink()
            except OSError:
                pass


def build_project_wheel(
    project_dir: Optional[Path | str] = None,
    output_dir: Optional[Path | str] = None,
    clean_before_build: bool = True
) -> Path:
    """Builds a .whl binary for the project located at project_dir.
    
    Args:
        project_dir: Path to directory containing pyproject.toml. Defaults to current directory.
        output_dir: Destination directory for the .whl artifact. Defaults to <project_dir>/dist.
        clean_before_build: Whether to delete existing .whl files in output_dir before building.

    Returns:
        Path to the compiled .whl file.
        
    Raises:
        PackagingError: If pyproject.toml is missing or build command fails.
    """
    proj_path = Path(project_dir or Path.cwd()).resolve()
    pyproject = proj_path / "pyproject.toml"

    if not pyproject.exists():
        raise PackagingError(f"No pyproject.toml found in {proj_path}. Cannot build wheel.")

    out_path = Path(output_dir or (proj_path / "dist")).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    if clean_before_build:
        clean_dist(out_path)

    # First attempt: use python build module CLI
    cmd = [
        sys.executable,
        "-m",
        "build",
        "--wheel",
        "--outdir",
        str(out_path),
        str(proj_path)
    ]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        if proc.returncode != 0:
            raise PackagingError(
                f"Failed to build project wheel with exit code {proc.returncode}.\n"
                f"STDOUT:\n{proc.stdout}\n"
                f"STDERR:\n{proc.stderr}"
            )
    except FileNotFoundError as exc:
        raise PackagingError(f"Python interpreter could not execute build module: {exc}") from exc

    wheels = sorted(out_path.glob("*.whl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not wheels:
        raise PackagingError(f"Build completed but no .whl found in {out_path}")

    return wheels[0]
