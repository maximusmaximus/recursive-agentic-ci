"""Sandboxed Execution and Continuous Integration Runner.

Executes patches and test suites in isolated scratch environments,
preventing any corruption of main branches until strict test gates are passed.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Dict, Any, Tuple, Optional

class SandboxRunner:
    """Isolated environment for executing and validating candidate code modifications."""

    def __init__(self, timeout_seconds: int = 120):
        self.timeout_seconds = timeout_seconds

    def execute_in_sandbox(
        self,
        repo_path: str,
        patch_files: Dict[str, str],
        test_command: str = "python -m unittest discover tests"
    ) -> Dict[str, Any]:
        """Clone repo into isolated scratch workspace, apply patches, and execute test harness."""
        start_time = time.time()
        temp_dir = tempfile.mkdtemp(prefix="rec_ci_sandbox_")

        try:
            # Copy repository into sandbox
            self._copy_repo_contents(repo_path, temp_dir)

            # Apply candidate modifications
            for rel_path, content in patch_files.items():
                dest_path = os.path.join(temp_dir, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, "w", encoding="utf-8") as f:
                    f.write(content)

            # Run test verification
            env = os.environ.copy()
            # Set PYTHONPATH so sandbox imports its own isolated files
            env["PYTHONPATH"] = temp_dir + os.pathsep + env.get("PYTHONPATH", "")

            resolved_cmd = test_command
            if resolved_cmd.startswith("python ") and shutil.which("python") is None:
                resolved_cmd = f'"{sys.executable}" ' + resolved_cmd[len("python "):]

            proc = subprocess.run(
                resolved_cmd,
                shell=True,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=env
            )

            passed = (proc.returncode == 0)
            elapsed = round(time.time() - start_time, 2)

            return {
                "success": passed,
                "exit_code": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "elapsed_seconds": elapsed,
                "sandbox_dir": temp_dir
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Sandbox execution timed out after {self.timeout_seconds} seconds.",
                "elapsed_seconds": round(time.time() - start_time, 2),
                "sandbox_dir": temp_dir
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -2,
                "stdout": "",
                "stderr": f"Sandbox runner exception: {str(e)}",
                "elapsed_seconds": round(time.time() - start_time, 2),
                "sandbox_dir": temp_dir
            }
        finally:
            # Clean up sandbox directory
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

    def _copy_repo_contents(self, src: str, dst: str):
        skip_dirs = {".git", "__pycache__", "venv", ".venv", "node_modules"}
        for item in os.listdir(src):
            if item in skip_dirs:
                continue
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, ignore=shutil.ignore_patterns("*.pyc", "__pycache__"))
            else:
                shutil.copy2(s, d)

    def commit_verified_branch(
        self,
        repo_path: str,
        branch_name: str,
        patch_files: Dict[str, str],
        commit_message: str,
        base_branch: str = "main",
        merge_to_base: bool = False,
    ) -> Dict[str, Any]:
        """Materialize sandbox-verified patches onto an isolated git branch (or non-git directory)."""
        abs_repo = os.path.abspath(repo_path)
        git_dir = os.path.join(abs_repo, ".git")

        if not os.path.exists(git_dir):
            for rel_path, content in patch_files.items():
                dest = os.path.join(abs_repo, rel_path)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(content)
            return {
                "success": True,
                "mode": "filesystem_apply",
                "branch_name": branch_name,
                "commit_sha": None,
                "files_written": list(patch_files.keys()),
            }

        wt_dir = tempfile.mkdtemp(prefix="rec_ci_worktree_")
        try:
            # Resolve starting ref (base_branch if it exists, otherwise HEAD)
            ref_check = subprocess.run(
                ["git", "rev-parse", "--verify", base_branch],
                cwd=abs_repo,
                capture_output=True,
                text=True,
            )
            start_ref = base_branch if ref_check.returncode == 0 else "HEAD"

            wt_add = subprocess.run(
                ["git", "worktree", "add", "-B", branch_name, wt_dir, start_ref],
                cwd=abs_repo,
                capture_output=True,
                text=True,
            )
            if wt_add.returncode != 0:
                return {
                    "success": False,
                    "error": f"git worktree add failed: {wt_add.stderr.strip()}",
                }

            for rel_path, content in patch_files.items():
                dest = os.path.join(wt_dir, rel_path)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(content)
                subprocess.run(["git", "add", rel_path], cwd=wt_dir, check=True, capture_output=True)

            diff_check = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=wt_dir,
                capture_output=True,
            )
            commit_sha: Optional[str] = None
            if diff_check.returncode != 0:
                commit_proc = subprocess.run(
                    [
                        "git",
                        "-c", "user.name=Hermes Recursive CI",
                        "-c", "user.email=hermes-ci@noreply.local",
                        "commit",
                        "-m", commit_message,
                    ],
                    cwd=wt_dir,
                    capture_output=True,
                    text=True,
                )
                if commit_proc.returncode != 0:
                    return {
                        "success": False,
                        "error": f"git commit failed: {commit_proc.stderr.strip()}",
                    }
            sha_proc = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=wt_dir,
                capture_output=True,
                text=True,
            )
            commit_sha = sha_proc.stdout.strip() or None

            subprocess.run(["git", "worktree", "remove", "--force", wt_dir], cwd=abs_repo, capture_output=True)

            merged_to_base = False
            if merge_to_base:
                cur_branch = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=abs_repo,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                dirty = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=abs_repo,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                if cur_branch == base_branch and not dirty:
                    m_proc = subprocess.run(
                        [
                            "git",
                            "-c", "user.name=Hermes Recursive CI",
                            "-c", "user.email=hermes-ci@noreply.local",
                            "merge", "--ff-only", branch_name,
                        ],
                        cwd=abs_repo,
                        capture_output=True,
                        text=True,
                    )
                    merged_to_base = (m_proc.returncode == 0)

            return {
                "success": True,
                "mode": "git_branch",
                "branch_name": branch_name,
                "commit_sha": commit_sha,
                "merged_to_base": merged_to_base,
                "files_written": list(patch_files.keys()),
            }
        finally:
            if os.path.exists(wt_dir):
                subprocess.run(["git", "worktree", "remove", "--force", wt_dir], cwd=abs_repo, capture_output=True)
                shutil.rmtree(wt_dir, ignore_errors=True)
