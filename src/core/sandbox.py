"""Sandboxed Execution and Continuous Integration Runner.

Executes patches and test suites in isolated scratch environments,
preventing any corruption of main branches until strict test gates are passed.
"""
import os
import shutil
import subprocess
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

            proc = subprocess.run(
                test_command,
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
        skip_dirs = {".git", "__pycache__", "venv", ".venv"}
        for item in os.listdir(src):
            if item in skip_dirs:
                continue
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, ignore=shutil.ignore_patterns("*.pyc", "__pycache__"))
            else:
                shutil.copy2(s, d)
