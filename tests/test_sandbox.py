import os
import unittest
from src.core.sandbox import SandboxRunner

class TestSandboxRunner(unittest.TestCase):
    def setUp(self):
        self.runner = SandboxRunner(timeout_seconds=30)
        self.sample_repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples", "sample_forked_repo"))

    def test_sandbox_clean_run(self):
        # Run tests on existing repo without patches
        res = self.runner.execute_in_sandbox(
            repo_path=self.sample_repo,
            patch_files={},
            test_command="python -m unittest discover tests"
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["exit_code"], 0)

    def test_sandbox_failing_patch(self):
        # Apply patch that intentionally breaks a test
        broken_calc = (
            "class Calculator:\n"
            "    def compute(self, op, a, b):\n"
            "        return -999999\n"
            "    def is_prime(self, n):\n"
            "        return False\n"
        )
        res = self.runner.execute_in_sandbox(
            repo_path=self.sample_repo,
            patch_files={"calculator.py": broken_calc},
            test_command="python -m unittest discover tests"
        )
        self.assertFalse(res["success"])
        self.assertNotEqual(res["exit_code"], 0)

if __name__ == "__main__":
    unittest.main()
