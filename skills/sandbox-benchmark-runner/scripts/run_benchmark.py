"""Helper script to execute and benchmark test suites in an isolated sandbox."""
import argparse
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from src.core.sandbox import SandboxRunner

def main():
    parser = argparse.ArgumentParser(description="Benchmark test suite execution in isolated sandbox")
    parser.add_argument("--path", required=True, help="Target repository path")
    parser.add_argument("--test-cmd", default="python -m unittest discover tests", help="Test command to run")
    args = parser.parse_args()

    print(f"[*] Provisioning isolated sandbox worktree for `{args.path}`...")
    runner = SandboxRunner(timeout_seconds=60)
    res = runner.execute_in_sandbox(
        repo_path=args.path,
        patch_files={},
        test_command=args.test_cmd
    )

    print("\n=======================================================")
    print(" SANDBOX EXECUTION & BENCHMARK REPORT")
    print("=======================================================")
    print(f"• Status:        {'PASSED' if res['success'] else 'FAILED'}")
    print(f"• Exit Code:     {res['exit_code']}")
    print(f"• Elapsed Time:  {res['elapsed_seconds']} seconds")
    if res['stdout']:
        print(f"\nTest Output:\n{res['stdout']}")
    if res['stderr']:
        print(f"\nErrors:\n{res['stderr']}")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
