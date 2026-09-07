"""Tests for the wheel packaging module."""

from pathlib import Path
import pytest
from databricks_forge.core.packaging import (
    find_project_root,
    clean_dist,
    build_project_wheel,
    PackagingError,
)
from databricks_forge.core.generator import ProjectGenerator


def test_clean_dist(tmp_path: Path):
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    f1 = dist_dir / "test-0.1.0-py3-none-any.whl"
    f2 = dist_dir / "keep_me.txt"
    f1.write_text("fake wheel")
    f2.write_text("info")

    clean_dist(dist_dir)

    assert not f1.exists()
    assert f2.exists()


def test_build_project_wheel_fails_without_pyproject(tmp_path: Path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with pytest.raises(PackagingError, match="No pyproject.toml found"):
        build_project_wheel(project_dir=empty_dir)


def test_build_project_wheel_success(tmp_path: Path):
    # Generate a lightweight project
    generator = ProjectGenerator()
    proj_dir = tmp_path / "sample_pkg"
    generator.create("sample_pkg", proj_dir)

    # Build wheel
    wheel = build_project_wheel(project_dir=proj_dir)

    assert wheel.exists()
    assert wheel.suffix == ".whl"
    assert "sample_pkg" in wheel.name
