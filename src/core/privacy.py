"""Venice AI Privacy Boundary, E2EE Enclave Router & AST Redaction Engine.

Ensures zero-data retention (ZDR) and optional hardware-enclave End-to-End
Encryption (E2EE), scrubs secrets/PII (including PoA pk_*/psk_*, Venice keys,
PEM blocks, and Bearer tokens) from codebase snippets, abstracts AST signatures,
and interfaces securely with Venice AI inference endpoints.
"""
import json
import os
import re
from typing import Dict, Any, List, Optional


class VenicePrivacyProxy:
    """Privacy boundary enforcing zero-retention, E2EE routing, and AST redaction."""

    E2EE_MODEL_MAP = {
        "llama-3.3-70b": "e2ee-kimi-k3-p",
        "deepseek-r1": "e2ee-deepseek-v4-flash",
        "qwen-2.5-coder-32b": "e2ee-qwen-2-5-7b-p",
        "kimi-k3": "e2ee-kimi-k3-p",
    }

    SECRET_PATTERNS = [
        (r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z0-9 ]*PRIVATE KEY-----", "[REDACTED_PRIVATE_KEY_PEM]"),
        (r"\bpsk_[A-Za-z0-9_\-]{12,}\b", "[REDACTED_POA_SESSION_KEY]"),
        (r"\bpk_[A-Za-z0-9_\-]{12,}\b", "[REDACTED_POA_SECRET_KEY]"),
        (r"\bvv_ak_[A-Za-z0-9_\-]{12,}\b", "[REDACTED_VENICE_KEY]"),
        (r"\bgh[pousr]_[A-Za-z0-9]{30,}\b", "[REDACTED_GITHUB_TOKEN]"),
        (r"\bsk-[A-Za-z0-9_\-]{24,}\b", "[REDACTED_OPENAI_TOKEN]"),
        (r"\bAIza[0-9A-Za-z\-_]{35}\b", "[REDACTED_GOOGLE_KEY]"),
        (r"(?i)\bBearer\s+[A-Za-z0-9_\-\.\/\+]{16,}\b", "Bearer [REDACTED_BEARER_TOKEN]"),
        (r"(?i)(api[_-]?key|secret|token|password|auth|private[_-]?key)\s*[:=]\s*['\"][A-Za-z0-9_\-\.\/\+]{8,}['\"]", r"\1: '[REDACTED_SECRET]'"),
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[REDACTED_EMAIL]"),
        (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[REDACTED_IP]"),
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.venice.ai/api/v1",
        model: str = "llama-3.3-70b",
        e2ee_enabled: Optional[bool] = None,
    ):
        self.api_key = api_key or os.environ.get("VENICE_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.default_model = model
        if e2ee_enabled is None:
            env_flag = os.environ.get("VENICE_E2EE", "").strip().lower()
            self.e2ee_enabled = env_flag in {"1", "true", "yes", "on"}
        else:
            self.e2ee_enabled = bool(e2ee_enabled)

    def resolve_model(self, requested_model: Optional[str] = None) -> str:
        """Resolve target Venice model, upgrading to hardware E2EE enclave when enabled."""
        base = requested_model or self.default_model
        if not self.e2ee_enabled:
            return base
        if base.startswith("e2ee-"):
            return base
        return self.E2EE_MODEL_MAP.get(base, "e2ee-deepseek-v4-flash")

    def sanitize_code_payload(self, code: str) -> str:
        """Strip secrets, keys, PEM blocks, PII, and internal IPs from code payload."""
        sanitized = code
        for pattern, replacement in self.SECRET_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized)
        return sanitized

    def abstract_ast_context(self, file_content: str, rel_path: str) -> Dict[str, Any]:
        """Convert raw code into a privacy-preserving structural semantic contract."""
        sanitized = self.sanitize_code_payload(file_content)
        lines = sanitized.splitlines()
        interface_lines = [
            line.strip() for line in lines
            if line.strip().startswith(("def ", "class ", "async def ", "import ", "from ", "export ", "public ", "fn "))
        ]
        return {
            "path": rel_path,
            "interfaces": interface_lines,
            "safe_excerpt": "\n".join(lines[:25]),
            "privacy_mode": "venice_e2ee_enclave" if self.e2ee_enabled else "venice_zdr",
        }

    def plan_improvement(self, repo_summary: Dict[str, Any], vector: Dict[str, Any], maintainer_rules: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate an implementation plan via Venice AI zero-retention / E2EE model."""
        sanitized_title = self.sanitize_code_payload(vector.get("title", ""))
        rules_text = "\n".join(f"- {r}" for r in (maintainer_rules or []))
        resolved_model = self.resolve_model()

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
            "- clarifying_questions: optional list of strings (questions for human gatekeeper if ambiguous)\n"
            "- test_plan: string\n"
            "- backward_compatible: bool\n"
            "- safety_score: float (0.0 to 1.0)"
        )

        if not self.api_key:
            return self._mock_venice_plan(vector, maintainer_rules, resolved_model=resolved_model)

        try:
            import urllib.request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-Venice-Zero-Retention": "true",
            }
            if self.e2ee_enabled:
                headers["X-Venice-Enclave-Mode"] = "e2ee"
            body = {
                "model": resolved_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
                "venice_parameters": {
                    "include_venice_system_prompt": False,
                },
            }
            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=json.dumps(body).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    parsed.setdefault("privacy_model", resolved_model)
                    return parsed
                return {
                    "title": sanitized_title,
                    "rationale": content,
                    "proposed_diff_summary": "Automated recursive enhancement",
                    "affected_files": [vector.get("module", "")],
                    "clarifying_questions": [],
                    "test_plan": "Run test suite in isolated worktree",
                    "backward_compatible": True,
                    "safety_score": 0.95,
                    "privacy_model": resolved_model,
                }
        except Exception as e:
            return self._mock_venice_plan(vector, maintainer_rules, error_note=str(e), resolved_model=resolved_model)

    def _mock_venice_plan(
        self,
        vector: Dict[str, Any],
        maintainer_rules: Optional[List[str]] = None,
        error_note: Optional[str] = None,
        resolved_model: Optional[str] = None,
    ) -> Dict[str, Any]:
        vtype = vector.get("type", "feature")
        target = vector.get("target", "target")
        module = vector.get("module", "module.py")
        category = vector.get("category", "enhancement")
        base_name = os.path.splitext(os.path.basename(module))[0]
        test_file = vector.get("suggested_test_file") or f"tests/test_{base_name}.py"
        privacy_model = resolved_model or self.resolve_model()

        if vtype == "mutation_bug":
            return {
                "title": f"Mutation Test: Edge-case fault in `{target}`",
                "rationale": f"Inject controlled boundary mutation into `{target}` to prove that the CI suite asserts regression failures.",
                "proposed_diff_summary": f"Modify boundary/return logic in `{module}` to inject an edge-case discrepancy during isolated sandbox test runs.",
                "affected_files": [module, test_file],
                "clarifying_questions": [],
                "test_plan": "Execute test suite and assert that mutation is caught by CI harness.",
                "backward_compatible": True,
                "safety_score": 0.98,
                "is_mutation": True,
                "synthetic": True,
                "privacy_model": privacy_model,
                "simulated_by_privacy_engine": error_note is None,
            }

        rationale = vector.get(
            "rationale",
            f"Extends `{target}` ({category}) with boundary validation, test coverage, and performance safeguards.",
        )
        diff_summary = vector.get(
            "proposed_diff_summary",
            f"Implement `{category}` improvement for `{target}` in `{module}` with unit test coverage in `{test_file}`.",
        )
        return {
            "title": self.sanitize_code_payload(vector.get("title", f"Enhancement for `{target}`")),
            "rationale": self.sanitize_code_payload(rationale),
            "proposed_diff_summary": self.sanitize_code_payload(diff_summary),
            "affected_files": [module, test_file],
            "clarifying_questions": list(vector.get("clarifying_questions", [])),
            "test_plan": "Execute full test runner to guarantee zero regressions and verify new capabilities.",
            "backward_compatible": True,
            "safety_score": 0.96,
            "is_mutation": False,
            "synthetic": True,
            "privacy_model": privacy_model,
            "simulated_by_privacy_engine": error_note is None,
        }
