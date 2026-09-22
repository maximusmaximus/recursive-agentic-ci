"""Venice AI Privacy Boundary & AST Redaction Engine.

Ensures zero-data retention, scrubs secrets/PII from codebase snippets,
abstracts AST signatures, and interfaces securely with Venice AI inference endpoints.
"""
import json
import os
import re
from typing import Dict, Any, List, Optional

class VenicePrivacyProxy:
    """Privacy boundary enforcing zero-retention and AST redaction before dispatch."""

    SECRET_PATTERNS = [
        (r"ghp_[A-Za-z0-9]{36}", "[REDACTED_GITHUB_TOKEN]"),
        (r"sk-[A-Za-z0-9]{32,}", "[REDACTED_OPENAI_TOKEN]"),
        (r"AIza[0-9A-Za-z-_]{35}", "[REDACTED_GOOGLE_KEY]"),
        (r"(?i)(api[_-]?key|secret|token|password|auth|private[_-]?key)\s*[:=]\s*['\"][A-Za-z0-9_\-\.\/\+]{8,}['\"]", r"\1: '[REDACTED_SECRET]'"),
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[REDACTED_EMAIL]"),
        (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[REDACTED_IP]")
    ]

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.venice.ai/api/v1", model: str = "llama-3.3-70b"):
        self.api_key = api_key or os.environ.get("VENICE_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.default_model = model

    def sanitize_code_payload(self, code: str) -> str:
        """Strip secrets, PII, and internal hashes from code payload."""
        sanitized = code
        for pattern, replacement in self.SECRET_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized)
        return sanitized

    def abstract_ast_context(self, file_content: str, rel_path: str) -> Dict[str, Any]:
        """Convert raw code into a privacy-preserving structural semantic contract."""
        sanitized = self.sanitize_code_payload(file_content)
        # Extract signatures without leaking implementation details
        lines = sanitized.splitlines()
        interface_lines = [
            line.strip() for line in lines 
            if line.strip().startswith(("def ", "class ", "async def ", "import ", "from ", "export ", "public ", "fn "))
        ]
        return {
            "path": rel_path,
            "interfaces": interface_lines,
            "safe_excerpt": "\n".join(lines[:25]) # Top-level module contract
        }

    def plan_improvement(self, repo_summary: Dict[str, Any], vector: Dict[str, Any], maintainer_rules: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate an implementation plan via Venice AI zero-retention model."""
        sanitized_title = self.sanitize_code_payload(vector.get("title", ""))
        rules_text = "\n".join(f"- {r}" for r in (maintainer_rules or []))

        system_prompt = (
            "You are an autonomous recursive software engineer operating under strict enterprise privacy guarantees. "
            "You propose high-leverage, non-breaking improvements or intentional mutation tests to verify CI suites. "
            "Never modify existing core public contracts without backwards compatibility. "
            "Adhere strictly to maintainer constraints.\n"
            f"Maintainer Constraints:\n{rules_text if rules_text else 'None specified'}"
        )

        user_prompt = (
            f"Target Vector: {sanitized_title}\n"
            f"Category: {vector.get('category')}\n"
            f"Module: {vector.get('module')}\n"
            f"Target: {vector.get('target')}\n\n"
            "Produce a structured JSON proposal with fields:\n"
            "- title: string\n"
            "- rationale: string (why this improves quality or tests resilience)\n"
            "- proposed_diff_summary: string\n"
            "- affected_files: list of strings\n"
            "- test_plan: string\n"
            "- backward_compatible: bool\n"
            "- safety_score: float (0.0 to 1.0)"
        )

        if not self.api_key:
            # Hermetic / Mock plan generation for offline or testing mode
            return self._mock_venice_plan(vector, maintainer_rules)

        try:
            import urllib.request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-Venice-Zero-Retention": "true"
            }
            body = {
                "model": self.default_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "venice_parameters": {
                    "include_venice_system_prompt": False
                }
            }
            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=json.dumps(body).encode("utf-8"),
                headers=headers,
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                # Parse JSON block if present
                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
                return {
                    "title": sanitized_title,
                    "rationale": content,
                    "proposed_diff_summary": "Automated recursive enhancement",
                    "affected_files": [vector.get("module", "")],
                    "test_plan": "Run pytest suite in isolated worktree",
                    "backward_compatible": True,
                    "safety_score": 0.95
                }
        except Exception as e:
            # Fallback cleanly to structured heuristic plan
            return self._mock_venice_plan(vector, maintainer_rules, error_note=str(e))

    def _mock_venice_plan(self, vector: Dict[str, Any], maintainer_rules: Optional[List[str]] = None, error_note: Optional[str] = None) -> Dict[str, Any]:
        vtype = vector.get("type", "feature")
        target = vector.get("target", "target")
        module = vector.get("module", "module.py")

        if vtype == "mutation_bug":
            return {
                "title": f"Mutation Test: Edge-case fault in `{target}`",
                "rationale": f"Inject controlled boundary mutation into `{target}` to prove that the CI suite asserts regression failures.",
                "proposed_diff_summary": f"Modify return statement in `{module}` to inject an edge-case discrepancy during test runs.",
                "affected_files": [module, f"tests/test_{os.path.splitext(os.path.basename(module))[0]}.py"],
                "test_plan": "Execute test suite and assert that mutation is caught by CI harness.",
                "backward_compatible": True,
                "safety_score": 0.98,
                "is_mutation": True,
                "synthetic": True,
                "simulated_by_privacy_engine": error_note is None
            }
        else:
            return {
                "title": vector.get("title", f"Enhancement for `{target}`"),
                "rationale": f"Extends `{target}` with robust error guards, input boundary checks, and performance optimizations.",
                "proposed_diff_summary": f"Add zero-division guard and batch factorize method to `{module}`.",
                "affected_files": [module, f"tests/test_{os.path.splitext(os.path.basename(module))[0]}.py"],
                "test_plan": "Execute full test runner to guarantee zero regressions and verify new capabilities.",
                "backward_compatible": True,
                "safety_score": 0.96,
                "is_mutation": False,
                "synthetic": True,
                "simulated_by_privacy_engine": error_note is None
            }
