"""Helper script to run a mutation resilience probe on a repository."""
import argparse
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from src.core.sandbox import SandboxRunner

def main():
    parser = argparse.ArgumentParser(description="Run mutation resilience probe")
    parser.add_argument("--path", required=True, help="Target repository path")
    parser.add_argument("--module", default="calculator.py", help="Module to mutate")
    args = parser.parse_args()

    target_file = os.path.join(args.path, args.module)
    if not os.path.exists(target_file):
        print(f"[!] Target module not found: {target_file}")
        sys.exit(1)

    with open(target_file, "r", encoding="utf-8") as f:
        original = f.read()

    # Create mutant by injecting an inverted calculation
    mutant = original.replace("return a + b", "return a - b")
    if mutant == original:
        mutant = original.replace("return True", "return False")

    print(f"[*] Injected controlled fault into `{args.module}`")
    print("[*] Running test suite in isolated scratch sandbox...")

    runner = SandboxRunner(timeout_seconds=30)
    res = runner.execute_in_sandbox(
        repo_path=args.path,
        patch_files={args.module: mutant}
    )

    if not res["success"]:
        print("\n✅ MUTATION KILLED: Test suite caught the regression as expected!")
        print("Your CI test harness is robust against this fault.")
    else:
        print("\n🚨 CI BLINDSPOT DETECTED: The test suite PASSED despite injected logic regression!")
        print("Hermes recommends adding a boundary assertion for this module.")

if __name__ == "__main__":
    main()
