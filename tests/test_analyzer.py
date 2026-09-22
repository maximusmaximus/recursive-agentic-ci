import os
import unittest
from src.core.analyzer import RepoAnalyzer

class TestRepoAnalyzer(unittest.TestCase):
    def setUp(self):
        # Target our sample forked repo
        self.sample_repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples", "sample_forked_repo"))

    def test_audit_structure(self):
        analyzer = RepoAnalyzer(self.sample_repo)
        report = analyzer.audit()

        self.assertGreater(report["total_files"], 0)
        self.assertGreater(report["total_lines"], 0)
        self.assertGreaterEqual(report["test_suite_count"], 1)
        self.assertIn("unittest", report["test_frameworks"])
        self.assertGreater(report["health_score"], 50.0)

    def test_vector_discovery(self):
        analyzer = RepoAnalyzer(self.sample_repo)
        report = analyzer.audit()

        feature_vectors = report["feature_vectors"]
        mutation_vectors = report["mutation_bug_vectors"]

        self.assertGreater(len(feature_vectors), 0)
        self.assertGreater(len(mutation_vectors), 0)

        # Verify calculator enhancement vector is captured
        has_calc = any("Calculator" in v.get("target", "") for v in feature_vectors)
        self.assertTrue(has_calc)

if __name__ == "__main__":
    unittest.main()
