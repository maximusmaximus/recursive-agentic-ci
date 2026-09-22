"""Repository Analyzer and AST Inspector.

Scans an arbitrary target repository, maps AST structures, detects test frameworks,
and extracts both feature enhancement vectors and mutation/bug resilience testing vectors.
"""
import ast
import os
import re
from typing import Dict, List, Any, Optional

class RepoAnalyzer:
    """Static analysis engine for repository structure and enhancement vectors."""

    SUPPORTED_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".go": "go",
        ".rs": "rust"
    }

    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)
        if not os.path.exists(self.repo_path):
            raise FileNotFoundError(f"Target repository path does not exist: {self.repo_path}")

    def audit(self) -> Dict[str, Any]:
        """Perform a full audit of the target repository."""
        files = self._collect_files()
        file_metrics = []
        total_lines = 0
        ast_nodes = []
        test_suites = []

        for fpath in files:
            rel_path = os.path.relpath(fpath, self.repo_path)
            lang = self._detect_language(fpath)
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            lines = len(content.splitlines())
            total_lines += lines

            is_test = self._is_test_file(rel_path)
            if is_test:
                test_suites.append({
                    "file": rel_path,
                    "framework": self._detect_test_framework(content)
                })

            parsed_info = {}
            if lang == "python":
                parsed_info = self._parse_python_ast(content, rel_path)
                ast_nodes.append(parsed_info)

            file_metrics.append({
                "path": rel_path,
                "language": lang,
                "lines": lines,
                "is_test": is_test,
                "symbols": parsed_info.get("symbols", [])
            })

        # Discover enhancement vectors
        feature_vectors = self._discover_feature_vectors(ast_nodes)
        mutation_bug_vectors = self._discover_mutation_vectors(ast_nodes)

        return {
            "repo_path": self.repo_path,
            "total_files": len(files),
            "total_lines": total_lines,
            "test_suite_count": len(test_suites),
            "test_frameworks": list({t["framework"] for t in test_suites if t["framework"]}),
            "files": file_metrics,
            "feature_vectors": feature_vectors,
            "mutation_bug_vectors": mutation_bug_vectors,
            "health_score": self._compute_health_score(total_lines, len(test_suites), len(feature_vectors))
        }

    def _collect_files(self) -> List[str]:
        collected = []
        skip_dirs = {".git", "__pycache__", "node_modules", "venv", ".venv", "dist", "build"}
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for f in files:
                ext = os.path.splitext(f)[1]
                if ext in self.SUPPORTED_EXTENSIONS or f in {"Dockerfile", "Makefile"}:
                    collected.append(os.path.join(root, f))
        return collected

    def _detect_language(self, path: str) -> str:
        ext = os.path.splitext(path)[1]
        return self.SUPPORTED_EXTENSIONS.get(ext, "unknown")

    def _is_test_file(self, rel_path: str) -> bool:
        normalized = rel_path.replace("\\", "/").lower()
        return "test" in normalized or "spec" in normalized

    def _detect_test_framework(self, content: str) -> str:
        if "import unittest" in content:
            return "unittest"
        if "import pytest" in content or "def test_" in content:
            return "pytest"
        if "describe(" in content or "it(" in content:
            return "jest/mocha"
        return "custom"

    def _parse_python_ast(self, code: str, rel_path: str) -> Dict[str, Any]:
        symbols = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    symbols.append({
                        "type": "class",
                        "name": node.name,
                        "line": node.lineno,
                        "methods": methods
                    })
                elif isinstance(node, ast.FunctionDef):
                    args = [arg.arg for arg in node.args.args]
                    symbols.append({
                        "type": "function",
                        "name": node.name,
                        "line": node.lineno,
                        "args": args
                    })
        except SyntaxError:
            pass
        return {"file": rel_path, "symbols": symbols}

    def _discover_feature_vectors(self, ast_nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        vectors = []
        for node in ast_nodes:
            fpath = node.get("file", "")
            if "test" in fpath.lower():
                continue
            for sym in node.get("symbols", []):
                if sym.get("type") == "class":
                    cname = sym.get("name")
                    methods = sym.get("methods", [])
                    if "Calculator" in cname and "factorize" not in methods:
                        vectors.append({
                            "type": "feature",
                            "module": fpath,
                            "target": cname,
                            "title": f"Add prime factorization & batch math to `{cname}`",
                            "impact": "high",
                            "category": "algorithmic_expansion"
                        })
                    if "DataStore" in cname or "Store" in cname:
                        vectors.append({
                            "type": "feature",
                            "module": fpath,
                            "target": cname,
                            "title": f"Add indexing & search cache to `{cname}`",
                            "impact": "medium",
                            "category": "performance_optimization"
                        })
                elif sym.get("type") == "function":
                    fname = sym.get("name")
                    if fname == "compute":
                        vectors.append({
                            "type": "feature",
                            "module": fpath,
                            "target": fname,
                            "title": "Add strict input validation & error taxonomy to `compute`",
                            "impact": "medium",
                            "category": "robustness"
                        })
        return vectors

    def _discover_mutation_vectors(self, ast_nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify intentional fault-injection points to test CI suite resilience."""
        mutations = []
        for node in ast_nodes:
            fpath = node.get("file", "")
            if "test" in fpath.lower():
                continue
            for sym in node.get("symbols", []):
                if sym.get("type") == "function" or sym.get("type") == "class":
                    mutations.append({
                        "type": "mutation_bug",
                        "module": fpath,
                        "target": sym.get("name"),
                        "title": f"Inject edge-case fault in `{sym.get('name')}` (Resilience Verification)",
                        "impact": "medium",
                        "category": "mutation_testing",
                        "hypothesis": "Verify that continuous integration unit tests trigger a failure if logic regressions occur."
                    })
        return mutations

    def _compute_health_score(self, total_lines: int, test_count: int, vector_count: int) -> float:
        score = 70.0
        if test_count > 0:
            score += 15.0
        if total_lines > 0 and (test_count / max(1, total_lines // 100)) >= 1:
            score += 10.0
        score -= min(15.0, vector_count * 2.0)
        return max(10.0, min(100.0, round(score, 1)))
