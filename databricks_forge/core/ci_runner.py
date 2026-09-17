"""CI Quality Gate Runner for Databricks Forge.

Executes local pytest suites and verifies CI status before allowing Databricks job dispatches.
"""

from __future__ import annotations

import asyncio
import logging
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CIQualityGateRunner:
    """Automates CI execution and verification for generated ETL pipelines."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path.cwd()

    async def run_local_tests_async(
        self,
        test_path: Optional[str] = None,
        timeout_sec: int = 90,
    ) -> Dict[str, Any]:
        """Runs pytest asynchronously and captures metrics, logs, and quality status."""
        cmd = [sys.executable, "-m", "pytest", "-v"]
        if test_path:
            cmd.append(test_path)
        else:
            cmd.append("tests")

        start_time = time.time()
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.base_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_sec,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.communicate()
                return {
                    "success": False,
                    "exit_code": -1,
                    "duration_sec": round(time.time() - start_time, 2),
                    "summary": f"Timeout após {timeout_sec}s executando testes.",
                    "passed": 0,
                    "failed": 1,
                    "output": f"Execution timed out after {timeout_sec} seconds.",
                }

            exit_code = process.returncode or 0
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            output = f"{stdout}\n{stderr}".strip()
            duration = round(time.time() - start_time, 2)

            passed_count, failed_count = self._parse_pytest_summary(output)

            success = (exit_code == 0)
            if success:
                summary = f"100% Aprovado ({passed_count} testes passaram em {duration}s)"
            else:
                summary = f"Falha na esteira ({failed_count} falhas, {passed_count} passaram em {duration}s)"

            return {
                "success": success,
                "exit_code": exit_code,
                "duration_sec": duration,
                "passed": passed_count,
                "failed": failed_count,
                "summary": summary,
                "output": output,
            }
        except Exception as exc:
            logger.exception("Error executing local tests")
            return {
                "success": False,
                "exit_code": -1,
                "duration_sec": round(time.time() - start_time, 2),
                "summary": f"Erro interno ao invocar pytest: {str(exc)}",
                "passed": 0,
                "failed": 1,
                "output": str(exc),
            }

    def run_local_tests(
        self,
        test_path: Optional[str] = None,
        timeout_sec: int = 90,
    ) -> Dict[str, Any]:
        """Synchronous wrapper for run_local_tests_async."""
        return asyncio.run(self.run_local_tests_async(test_path=test_path, timeout_sec=timeout_sec))

    def _parse_pytest_summary(self, output: str) -> tuple[int, int]:
        """Extracts passed and failed counts from pytest output string."""
        passed = 0
        failed = 0

        # Look for e.g. "2 passed" or "1 failed, 2 passed"
        passed_match = re.search(r"(\d+)\s+passed", output)
        if passed_match:
            passed = int(passed_match.group(1))

        failed_match = re.search(r"(\d+)\s+failed", output)
        if failed_match:
            failed = int(failed_match.group(1))

        # Look for error count as well
        error_match = re.search(r"(\d+)\s+error", output)
        if error_match:
            failed += int(error_match.group(1))

        return passed, failed

    def check_github_ci(self, commit_sha: str, timeout_sec: int = 60) -> Dict[str, Any]:
        """Checks GitHub Actions CI run status for a given commit if `gh` CLI is installed."""
        if not shutil.which("gh"):
            return {
                "available": False,
                "status": "skipped",
                "message": "GitHub CLI ('gh') não instalado no ambiente local. Quality gate local validado via pytest.",
            }

        try:
            res = subprocess.run(
                ["gh", "run", "list", "--commit", commit_sha, "--json", "status,conclusion,name,url"],
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_sec,
            )
            if res.returncode == 0:
                import json
                runs = json.loads(res.stdout) if res.stdout.strip() else []
                if runs:
                    latest = runs[0]
                    return {
                        "available": True,
                        "status": latest.get("status"),
                        "conclusion": latest.get("conclusion"),
                        "name": latest.get("name"),
                        "url": latest.get("url"),
                    }
            return {
                "available": True,
                "status": "pending",
                "message": "Esteira do GitHub Actions enfileirada para o commit.",
            }
        except Exception as e:
            return {"available": False, "status": "error", "message": str(e)}
