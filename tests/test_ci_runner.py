"""Unit tests for the CI Quality Gate Runner."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from databricks_forge.core.ci_runner import CIQualityGateRunner


def test_parse_pytest_summary():
    runner = CIQualityGateRunner()

    passed, failed = runner._parse_pytest_summary("=== 5 passed, 2 warnings in 0.45s ===")
    assert passed == 5
    assert failed == 0

    passed, failed = runner._parse_pytest_summary("=== 1 failed, 4 passed, 1 error in 1.20s ===")
    assert passed == 4
    assert failed == 2


def test_run_local_tests_success(tmp_path: Path):
    runner = CIQualityGateRunner(base_dir=tmp_path)

    mock_proc = AsyncMock()
    mock_proc.returncode = 0
    mock_proc.communicate.return_value = (b"=== 3 passed in 0.35s ===", b"")

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        result = asyncio.run(runner.run_local_tests_async(test_path="tests/test_dummy.py"))

    assert result["success"] is True
    assert result["exit_code"] == 0
    assert result["passed"] == 3
    assert result["failed"] == 0
    assert "100% Aprovado" in result["summary"]


def test_run_local_tests_failure(tmp_path: Path):
    runner = CIQualityGateRunner(base_dir=tmp_path)

    mock_proc = AsyncMock()
    mock_proc.returncode = 1
    mock_proc.communicate.return_value = (b"=== 1 failed, 2 passed in 0.50s ===", b"AssertionError")

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        result = runner.run_local_tests(test_path="tests/test_dummy.py")

    assert result["success"] is False
    assert result["exit_code"] == 1
    assert result["passed"] == 2
    assert result["failed"] == 1
    assert "Falha na esteira" in result["summary"]


def test_check_github_ci_no_gh(tmp_path: Path):
    runner = CIQualityGateRunner(base_dir=tmp_path)

    with patch("shutil.which", return_value=None):
        res = runner.check_github_ci("abc1234")
        assert res["available"] is False
        assert res["status"] == "skipped"


def test_check_github_ci_success(tmp_path: Path):
    runner = CIQualityGateRunner(base_dir=tmp_path)

    with patch("shutil.which", return_value="/usr/local/bin/gh"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='[{"status": "completed", "conclusion": "success", "name": "CI", "url": "https://github.com/..."}]',
        )
        res = runner.check_github_ci("abc1234")
        assert res["available"] is True
        assert res["status"] == "completed"
        assert res["conclusion"] == "success"
