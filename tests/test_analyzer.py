import os
import shutil
import tempfile
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

    def test_generalized_polyglot_and_ast_signals(self):
        tmp_repo = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(tmp_repo, "src"), exist_ok=True)
            os.makedirs(os.path.join(tmp_repo, "tests"), exist_ok=True)

            # File named inspector.py MUST NOT be misclassified as a 'spec' test file
            inspector_code = "\n".join([
                "class MetricsInspector:",
                "    def compute_ratio(self, total, count):",
                "        # FIXME: handle zero count edge case",
                "        return total / count",
                "",
                "    def silent_op(self, items):",
                "        try:",
                "            for val in items.values():",
                "                if val == 'target':",
                "                    return val",
                "        except Exception:",
                "            pass",
                *[f"    # padding line {i}" for i in range(20)],
            ])
            with open(os.path.join(tmp_repo, "src", "inspector.py"), "w", encoding="utf-8") as f:
                f.write(inspector_code)

            ts_code = "\n".join([
                "export class DomainRouter {",
                "  // TODO: cache DNS lookups",
                "}",
                "export async function resolveRecord(name: string) {",
                "  return name;",
                "}",
                *[f"// line {i}" for i in range(25)],
            ])
            with open(os.path.join(tmp_repo, "src", "router.ts"), "w", encoding="utf-8") as f:
                f.write(ts_code)

            with open(os.path.join(tmp_repo, "tests", "router.test.ts"), "w", encoding="utf-8") as f:
                f.write("import { describe, it } from 'vitest';\ndescribe('router', () => { it('works', () => {}); });\n")

            analyzer = RepoAnalyzer(tmp_repo)
            report = analyzer.audit()

            file_map = {item["path"].replace("\\", "/"): item for item in report["files"]}
            self.assertFalse(file_map["src/inspector.py"]["is_test"])
            self.assertTrue(file_map["tests/router.test.ts"]["is_test"])
            self.assertIn("vitest", report["test_frameworks"])

            categories = {v["category"] for v in report["feature_vectors"]}
            self.assertIn("robustness", categories)
            self.assertIn("observability_and_error_handling", categories)
            self.assertIn("performance_optimization", categories)
            self.assertIn("technical_debt", categories)
            self.assertIn("test_coverage_gap", categories)
        finally:
            shutil.rmtree(tmp_repo, ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
