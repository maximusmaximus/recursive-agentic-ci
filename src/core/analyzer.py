"""Repository Analyzer and Multi-Language AST Inspector.

Scans arbitrary target repositories (Python, TypeScript/JavaScript, Go, Rust),
maps AST structures and cyclomatic complexity, accurately detects test suites,
and discovers generalized feature, performance, coverage, and mutation vectors.
"""
import ast
import os
import re
import sys
from typing import Dict, List, Any, Optional, Set


class RepoAnalyzer:
    """Static analysis engine for repository structure and enhancement vectors."""

    SUPPORTED_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".mjs": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".go": "go",
        ".rs": "rust",
    }

    SKIP_DIRS = {
        ".git",
        "__pycache__",
        "node_modules",
        "venv",
        ".venv",
        "dist",
        "build",
        ".wrangler",
        ".pytest_cache",
        "_site",
        "sandboxes",
    }

    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)
        if not os.path.exists(self.repo_path):
            raise FileNotFoundError(f"Target repository path does not exist: {self.repo_path}")

    def audit(self) -> Dict[str, Any]:
        """Perform a full static and AST audit of the target repository."""
        files = self._collect_files()
        file_metrics: List[Dict[str, Any]] = []
        total_lines = 0
        parsed_modules: List[Dict[str, Any]] = []
        test_suites: List[Dict[str, Any]] = []
        tested_basenames: Set[str] = set()

        for fpath in files:
            rel_path = os.path.relpath(fpath, self.repo_path)
            lang = self._detect_language(fpath)
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            lines = len(content.splitlines())
            total_lines += lines

            is_test = self._is_test_file(rel_path)
            if is_test:
                framework = self._detect_test_framework(content, lang, rel_path)
                test_suites.append({
                    "file": rel_path,
                    "framework": framework,
                })
                tested_basenames.update(self._extract_tested_targets(rel_path, content))

            parsed_info: Dict[str, Any] = {"file": rel_path, "language": lang, "lines": lines, "is_test": is_test, "symbols": [], "signals": []}
            if lang == "python":
                parsed_info = self._parse_python_ast(content, rel_path, lines, is_test)
            elif lang in {"javascript", "typescript", "go", "rust"}:
                parsed_info = self._parse_polyglot_file(content, rel_path, lang, lines, is_test)

            parsed_modules.append(parsed_info)

            file_metrics.append({
                "path": rel_path,
                "language": lang,
                "lines": lines,
                "is_test": is_test,
                "symbols": parsed_info.get("symbols", []),
            })

        feature_vectors = self._discover_feature_vectors(parsed_modules, tested_basenames)
        mutation_bug_vectors = self._discover_mutation_vectors(parsed_modules)

        return {
            "repo_path": self.repo_path,
            "total_files": len(files),
            "total_lines": total_lines,
            "test_suite_count": len(test_suites),
            "test_frameworks": sorted({t["framework"] for t in test_suites if t["framework"]}),
            "files": file_metrics,
            "feature_vectors": feature_vectors,
            "mutation_bug_vectors": mutation_bug_vectors,
            "health_score": self._compute_health_score(total_lines, len(test_suites), len(feature_vectors)),
        }

    def _collect_files(self) -> List[str]:
        collected = []
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = sorted(d for d in dirs if d not in self.SKIP_DIRS)
            for f in sorted(files):
                ext = os.path.splitext(f)[1].lower()
                if ext in self.SUPPORTED_EXTENSIONS or f in {"Dockerfile", "Makefile"}:
                    collected.append(os.path.join(root, f))
        return collected

    def _detect_language(self, path: str) -> str:
        ext = os.path.splitext(path)[1].lower()
        return self.SUPPORTED_EXTENSIONS.get(ext, "unknown")

    def _is_test_file(self, rel_path: str) -> bool:
        """Accurately classify test files without substring false positives (e.g. 'inspector.py')."""
        normalized = rel_path.replace("\\", "/")
        parts = [p.lower() for p in normalized.split("/")]
        fname = parts[-1]
        dir_parts = set(parts[:-1])

        if dir_parts & {"test", "tests", "__tests__", "spec", "specs"}:
            return not fname.startswith("__init__.")

        stem, ext = os.path.splitext(fname)
        if stem.startswith("test_") or stem.endswith("_test") or stem.endswith(".test") or stem.endswith(".spec"):
            return True
        if fname in {"conftest.py"}:
            return True
        return False

    def _detect_test_framework(self, content: str, lang: str, rel_path: str) -> str:
        if lang == "python":
            if re.search(r"^\s*(?:import|from)\s+unittest\b", content, re.MULTILINE):
                return "unittest"
            if re.search(r"^\s*(?:import|from)\s+pytest\b", content, re.MULTILINE) or re.search(r"^\s*def\s+test_\w+", content, re.MULTILINE):
                return "pytest"
            return "python-custom"
        if lang in {"javascript", "typescript"}:
            if "node:test" in content:
                return "node:test"
            if "playwright" in content:
                return "playwright"
            if "vitest" in content:
                return "vitest"
            if re.search(r"^\s*(?:describe|it|test)\s*\(", content, re.MULTILINE):
                return "jest/mocha"
            return "js-custom"
        if lang == "go" and re.search(r"\bfunc\s+Test\w+\s*\(", content):
            return "go-test"
        if lang == "rust" and "#[test]" in content:
            return "cargo-test"
        return "custom"

    def _extract_tested_targets(self, rel_path: str, content: str) -> Set[str]:
        targets: Set[str] = set()
        fname = os.path.basename(rel_path).lower()
        stem = os.path.splitext(fname)[0]
        for prefix in ("test_",):
            if stem.startswith(prefix):
                targets.add(stem[len(prefix):])
        for suffix in ("_test", ".test", ".spec"):
            if stem.endswith(suffix):
                targets.add(stem[:-len(suffix)])
        for m in re.finditer(r"(?:from|import)\s+([A-Za-z0-9_\.]+)", content):
            last_seg = m.group(1).split(".")[-1].lower()
            if last_seg:
                targets.add(last_seg)
        return targets

    def _compute_complexity(self, node: ast.AST) -> int:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.IfExp, ast.comprehension)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += max(1, len(child.values) - 1)
        return complexity

    def _parse_python_ast(self, code: str, rel_path: str, lines: int, is_test: bool) -> Dict[str, Any]:
        symbols: List[Dict[str, Any]] = []
        signals: List[Dict[str, Any]] = []

        # Extract TODO / FIXME / HACK comments
        for idx, raw_line in enumerate(code.splitlines(), 1):
            m = re.search(r"#\s*(TODO|FIXME|HACK)\b[:\s]*(.*)", raw_line, re.IGNORECASE)
            if m:
                signals.append({
                    "kind": "todo_debt",
                    "line": idx,
                    "tag": m.group(1).upper(),
                    "detail": m.group(2).strip() or "Unresolved debt marker",
                })

        try:
            tree = ast.parse(code)
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    method_nodes = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    methods = [n.name for n in method_nodes]
                    max_method_complexity = max((self._compute_complexity(m) for m in method_nodes), default=1)
                    symbols.append({
                        "type": "class",
                        "name": node.name,
                        "line": node.lineno,
                        "methods": methods,
                        "has_docstring": ast.get_docstring(node) is not None,
                        "complexity": max_method_complexity,
                    })
                    for mnode in method_nodes:
                        self._inspect_callable_signals(mnode, f"{node.name}.{mnode.name}", signals)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [arg.arg for arg in node.args.args]
                    comp = self._compute_complexity(node)
                    symbols.append({
                        "type": "function",
                        "name": node.name,
                        "line": node.lineno,
                        "args": args,
                        "has_docstring": ast.get_docstring(node) is not None,
                        "complexity": comp,
                    })
                    self._inspect_callable_signals(node, node.name, signals)
        except SyntaxError:
            pass

        return {
            "file": rel_path,
            "language": "python",
            "lines": lines,
            "is_test": is_test,
            "symbols": symbols,
            "signals": signals,
        }

    def _inspect_callable_signals(self, fn_node: ast.AST, qualname: str, signals: List[Dict[str, Any]]):
        comp = self._compute_complexity(fn_node)
        if comp >= 10:
            signals.append({
                "kind": "high_complexity",
                "target": qualname,
                "line": getattr(fn_node, "lineno", 1),
                "complexity": comp,
            })

        has_try = any(isinstance(n, ast.Try) for n in ast.walk(fn_node))

        for sub in ast.walk(fn_node):
            # Detect bare or silent pass exception blocks
            if isinstance(sub, ast.ExceptHandler):
                is_silent_pass = len(sub.body) == 1 and isinstance(sub.body[0], ast.Pass)
                if sub.type is None or is_silent_pass:
                    signals.append({
                        "kind": "swallowed_exception",
                        "target": qualname,
                        "line": sub.lineno,
                    })

            # Detect unguarded division by variable divisor
            if isinstance(sub, ast.BinOp) and isinstance(sub.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                if isinstance(sub.right, ast.Name) and not has_try:
                    divisor_name = sub.right.id
                    src_guard = self._has_zero_guard(fn_node, divisor_name)
                    if not src_guard:
                        signals.append({
                            "kind": "unguarded_division",
                            "target": qualname,
                            "divisor": divisor_name,
                            "line": sub.lineno,
                        })

            # Detect linear scan over dict .values() inside lookup loops
            if isinstance(sub, ast.For):
                iter_node = sub.iter
                if isinstance(iter_node, ast.Call) and isinstance(iter_node.func, ast.Attribute):
                    if iter_node.func.attr == "values":
                        signals.append({
                            "kind": "linear_value_scan",
                            "target": qualname,
                            "line": sub.lineno,
                        })

    def _has_zero_guard(self, fn_node: ast.AST, var_name: str) -> bool:
        for n in ast.walk(fn_node):
            if isinstance(n, ast.Compare):
                names = [c.id for c in ast.walk(n) if isinstance(c, ast.Name)]
                has_zero = any(
                    isinstance(c, ast.Constant) and c.value == 0
                    for c in ast.walk(n)
                )
                if not has_zero and sys.version_info < (3, 8):
                    num_cls = getattr(ast, "Num", None)
                    if num_cls is not None:
                        has_zero = any(isinstance(c, num_cls) and c.n == 0 for c in ast.walk(n))
                if var_name in names and has_zero:
                    return True
        return False

    def _parse_polyglot_file(self, code: str, rel_path: str, lang: str, lines: int, is_test: bool) -> Dict[str, Any]:
        symbols: List[Dict[str, Any]] = []
        signals: List[Dict[str, Any]] = []

        for idx, raw_line in enumerate(code.splitlines(), 1):
            todo_m = re.search(r"(?://|#)\s*(TODO|FIXME|HACK)\b[:\s]*(.*)", raw_line, re.IGNORECASE)
            if todo_m:
                signals.append({
                    "kind": "todo_debt",
                    "line": idx,
                    "tag": todo_m.group(1).upper(),
                    "detail": todo_m.group(2).strip() or "Unresolved debt marker",
                })

            if lang in {"javascript", "typescript"}:
                cls_m = re.match(r"^\s*(?:export\s+)?class\s+([A-Za-z0-9_]+)", raw_line)
                if cls_m:
                    symbols.append({"type": "class", "name": cls_m.group(1), "line": idx, "methods": []})
                fn_m = re.match(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_]+)", raw_line)
                if fn_m:
                    symbols.append({"type": "function", "name": fn_m.group(1), "line": idx, "args": []})
            elif lang == "go":
                fn_m = re.match(r"^\s*func\s+(?:\([^)]+\)\s*)?([A-Za-z0-9_]+)\s*\(", raw_line)
                if fn_m:
                    symbols.append({"type": "function", "name": fn_m.group(1), "line": idx, "args": []})
            elif lang == "rust":
                fn_m = re.match(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z0-9_]+)", raw_line)
                if fn_m:
                    symbols.append({"type": "function", "name": fn_m.group(1), "line": idx, "args": []})

        return {
            "file": rel_path,
            "language": lang,
            "lines": lines,
            "is_test": is_test,
            "symbols": symbols,
            "signals": signals,
        }

    def _discover_feature_vectors(
        self,
        parsed_modules: List[Dict[str, Any]],
        tested_basenames: Set[str],
    ) -> List[Dict[str, Any]]:
        vectors: List[Dict[str, Any]] = []
        seen_keys: Set[str] = set()

        def _add(vec: Dict[str, Any]):
            key = f"{vec.get('module')}::{vec.get('target')}::{vec.get('category')}"
            if key not in seen_keys:
                seen_keys.add(key)
                vectors.append(vec)

        for mod in parsed_modules:
            fpath = mod.get("file", "")
            if mod.get("is_test"):
                continue

            fname = os.path.basename(fpath)
            stem = os.path.splitext(fname)[0].lower()

            # Domain-aware & structural class/function vectors
            for sym in mod.get("symbols", []):
                if sym.get("type") == "class":
                    cname = sym.get("name", "")
                    methods = sym.get("methods", [])
                    if "Calculator" in cname and "factorize" not in methods:
                        _add({
                            "type": "feature",
                            "module": fpath,
                            "target": cname,
                            "title": f"Add prime factorization & batch math to `{cname}`",
                            "impact": "high",
                            "category": "algorithmic_expansion",
                        })
                    if ("DataStore" in cname or cname.endswith("Store")) and not any("index" in m for m in methods):
                        _add({
                            "type": "feature",
                            "module": fpath,
                            "target": cname,
                            "title": f"Add secondary index & lookup cache to `{cname}`",
                            "impact": "medium",
                            "category": "performance_optimization",
                        })

            # Generalized AST signal vectors (works on ANY repository)
            for sig in mod.get("signals", []):
                kind = sig.get("kind")
                target = sig.get("target", stem)
                short_target = target.split(".")[-1]

                if kind == "unguarded_division":
                    _add({
                        "type": "feature",
                        "module": fpath,
                        "target": short_target,
                        "title": f"Add zero-division boundary guard & input validation to `{target}`",
                        "impact": "high",
                        "category": "robustness",
                    })
                elif kind == "linear_value_scan":
                    _add({
                        "type": "feature",
                        "module": fpath,
                        "target": short_target,
                        "title": f"Replace O(N) linear `.values()` scan in `{target}` with indexed lookup cache",
                        "impact": "medium",
                        "category": "performance_optimization",
                    })
                elif kind == "high_complexity":
                    _add({
                        "type": "feature",
                        "module": fpath,
                        "target": short_target,
                        "title": f"Decompose high-complexity `{target}` (CC={sig.get('complexity')}) and add boundary test coverage",
                        "impact": "medium",
                        "category": "refactoring_and_guards",
                    })
                elif kind == "swallowed_exception":
                    _add({
                        "type": "feature",
                        "module": fpath,
                        "target": short_target,
                        "title": f"Replace silent exception swallow in `{target}` with structured telemetry logging",
                        "impact": "medium",
                        "category": "observability_and_error_handling",
                    })
                elif kind == "todo_debt":
                    _add({
                        "type": "feature",
                        "module": fpath,
                        "target": stem,
                        "title": f"Resolve {sig.get('tag')} in `{fpath}:{sig.get('line')}` — {sig.get('detail')}",
                        "impact": "low",
                        "category": "technical_debt",
                    })

            # Untested non-trivial module detection
            if (
                mod.get("lines", 0) >= 25
                and stem not in {"__init__", "cli", "main", "setup"}
                and stem not in tested_basenames
                and mod.get("symbols")
            ):
                primary_target = mod["symbols"][0]["name"]
                _add({
                    "type": "feature",
                    "module": fpath,
                    "target": primary_target,
                    "title": f"Add dedicated unit test coverage suite for `{fpath}` (`{primary_target}`)",
                    "impact": "high",
                    "category": "test_coverage_gap",
                })

        return vectors

    def _discover_mutation_vectors(self, parsed_modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify intentional fault-injection points to test CI suite resilience."""
        mutations = []
        for mod in parsed_modules:
            fpath = mod.get("file", "")
            if mod.get("is_test"):
                continue
            for sym in mod.get("symbols", []):
                if sym.get("type") in {"function", "class"}:
                    mutations.append({
                        "type": "mutation_bug",
                        "module": fpath,
                        "target": sym.get("name"),
                        "title": f"Inject edge-case fault in `{sym.get('name')}` (Resilience Verification)",
                        "impact": "medium",
                        "category": "mutation_testing",
                        "hypothesis": "Verify that continuous integration unit tests trigger a failure if logic regressions occur.",
                    })
        return mutations

    def _compute_health_score(self, total_lines: int, test_count: int, vector_count: int) -> float:
        score = 70.0
        if test_count > 0:
            score += 15.0
        if total_lines > 0 and (test_count / max(1, total_lines // 150)) >= 0.5:
            score += 10.0
        score -= min(20.0, vector_count * 1.5)
        return max(10.0, min(100.0, round(score, 1)))
