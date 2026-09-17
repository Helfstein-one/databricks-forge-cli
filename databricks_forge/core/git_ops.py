"""Git Operations Utility for Databricks Forge CLI."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GitOpsManager:
    """Manages Git operations like status, add, commit, and push."""

    def __init__(self, repo_dir: Optional[Path] = None):
        self.repo_dir = repo_dir or Path.cwd()

    def _run_git(self, args: List[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git"] + args,
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            check=False,
        )

    def is_git_repo(self) -> bool:
        res = self._run_git(["rev-parse", "--is-inside-work-tree"])
        return res.returncode == 0 and res.stdout.strip() == "true"

    def get_current_branch(self) -> str:
        res = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if res.returncode == 0:
            return res.stdout.strip()
        return "main"

    def stage_files(self, file_paths: List[str]) -> bool:
        res = self._run_git(["add"] + file_paths)
        return res.returncode == 0

    def commit(self, message: str) -> Optional[str]:
        """Commits staged changes and returns the short commit hash."""
        res = self._run_git(["commit", "-m", message])
        if res.returncode != 0:
            logger.error(f"Git commit failed: {res.stderr}")
            return None
        rev = self._run_git(["rev-parse", "--short", "HEAD"])
        return rev.stdout.strip() if rev.returncode == 0 else "latest"

    def push(self, remote: str = "origin", branch: Optional[str] = None) -> Dict[str, Any]:
        """Pushes current branch to remote repository."""
        target_branch = branch or self.get_current_branch()
        res = self._run_git(["push", remote, target_branch])
        if res.returncode == 0:
            return {
                "success": True,
                "remote": remote,
                "branch": target_branch,
                "output": res.stdout.strip() or res.stderr.strip(),
            }
        return {
            "success": False,
            "remote": remote,
            "branch": target_branch,
            "error": res.stderr.strip(),
        }

    def commit_and_push(self, file_paths: List[str], message: str) -> Dict[str, Any]:
        """Stages specified files, commits, and pushes to remote."""
        if not self.is_git_repo():
            return {"success": False, "error": "Diretório não é um repositório Git válido."}

        staged = self.stage_files(file_paths)
        if not staged:
            return {"success": False, "error": "Falha ao adicionar arquivos com git add."}

        commit_hash = self.commit(message)
        if not commit_hash:
            return {"success": False, "error": "Falha ao realizar git commit."}

        push_res = self.push()
        push_res["commit_hash"] = commit_hash
        return push_res
