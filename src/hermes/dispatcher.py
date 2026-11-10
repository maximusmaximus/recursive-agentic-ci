"""Dynamic JIT Skill Dispatcher & AST RepoGenome Fingerprinter.

Prevents context window bloat by lazily loading skills only when triggered by
specific repository AST capabilities or inbound telemetry events.
"""
import ast
import os
from typing import Dict, Any, List, Set, Optional

class RepoGenome:
    """Static AST fingerprint of repository capabilities."""

    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)

    def compute_fingerprint(self) -> Dict[str, Any]:
        has_tests = False
        has_web_routes = False
        has_logging_or_telemetry = False
        has_complex_algorithms = False

        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "venv", ".venv", "node_modules", "dist", "build"}]
            rel_dir_parts = {p.lower() for p in os.path.relpath(root, self.repo_path).replace("\\", "/").split("/")}
            for f in files:
                fname_lower = f.lower()
                stem_lower, ext_lower = os.path.splitext(fname_lower)
                if (
                    rel_dir_parts & {"test", "tests", "__tests__", "spec", "specs"}
                    or stem_lower.startswith("test_")
                    or stem_lower.endswith(("_test", ".test", ".spec"))
                ):
                    has_tests = True

                if ext_lower in {".py", ".js", ".mjs", ".ts", ".tsx", ".go", ".rs"}:
                    try:
                        with open(os.path.join(root, f), "r", encoding="utf-8", errors="replace") as fp:
                            content = fp.read()
                            if any(k in content for k in ["route(", "@app.", "handle_request", "endpoint", "FastAPI", "Flask", "bottle", "express(", "Hono", "fetch("]):
                                has_web_routes = True
                            if any(k in content for k in ["sentry", "logging", "telemetry", "traceback", "datadog", "console.error"]):
                                has_logging_or_telemetry = True
                            if any(k in content for k in ["for ", "while ", "def factorize", "def is_prime", "search", "sort"]):
                                has_complex_algorithms = True
                    except Exception:
                        pass

        # Determine skill affinities based on AST markers
        affinities = {"recursive-ci"} # Always available
        if has_tests:
            affinities.add("sandbox-benchmark-runner")
            affinities.add("chaos-mutation-tester")
        if has_web_routes:
            affinities.add("product-analytics-optimizer")
        if has_logging_or_telemetry:
            affinities.add("telemetry-diagnostics")

        return {
            "has_tests": has_tests,
            "has_web_routes": has_web_routes,
            "has_logging_or_telemetry": has_logging_or_telemetry,
            "has_complex_algorithms": has_complex_algorithms,
            "skill_affinities": list(affinities)
        }

class DynamicSkillDispatcher:
    """Manages JIT loading and context eviction of Hermes skills."""

    SKILL_INDEX = {
        "recursive-ci": {
            "trigger_events": ["cron_dash", "manual_dash", "audit"],
            "required_affinity": None,
            "token_weight": 850
        },
        "telemetry-diagnostics": {
            "trigger_events": ["crash_alert", "stack_trace_ingest", "sentry_webhook"],
            "required_affinity": "telemetry-diagnostics",
            "token_weight": 1100
        },
        "product-analytics-optimizer": {
            "trigger_events": ["p95_latency_spike", "funnel_drop", "query_waterfall"],
            "required_affinity": "product-analytics-optimizer",
            "token_weight": 1250
        },
        "chaos-mutation-tester": {
            "trigger_events": ["resilience_audit", "mutation_probe", "security_check"],
            "required_affinity": "chaos-mutation-tester",
            "token_weight": 950
        },
        "sandbox-benchmark-runner": {
            "trigger_events": ["maintainer_approved", "run_sandbox", "benchmark_ram"],
            "required_affinity": "sandbox-benchmark-runner",
            "token_weight": 700
        }
    }

    def __init__(self, skills_dir: Optional[str] = None):
        self.skills_dir = skills_dir or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "skills")
        )
        self._mounted_skills: Set[str] = set()

    def get_micro_catalog(self) -> Dict[str, str]:
        """Returns ultra-compact (<120 tokens) index for the agent baseline prompt."""
        return {
            name: " | ".join(spec["trigger_events"])
            for name, spec in self.SKILL_INDEX.items()
        }

    def resolve_active_skills(self, event_type: str, repo_affinities: List[str]) -> List[str]:
        """Determine exactly which skills to mount for a given event and repository."""
        to_mount = []
        for skill_name, spec in self.SKILL_INDEX.items():
            if event_type in spec["trigger_events"]:
                req = spec["required_affinity"]
                if req is None or req in repo_affinities:
                    to_mount.append(skill_name)
        return to_mount

    def mount_skill(self, skill_name: str) -> Optional[str]:
        """JIT loads full SKILL.md into context."""
        skill_file = os.path.join(self.skills_dir, skill_name, "SKILL.md")
        if os.path.exists(skill_file):
            self._mounted_skills.add(skill_name)
            with open(skill_file, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def evict_skill(self, skill_name: str):
        """Purges skill from context after execution."""
        self._mounted_skills.discard(skill_name)

    def evict_all(self):
        """Restores context to bare baseline."""
        self._mounted_skills.clear()

    def estimate_tokens_saved(self, mounted_skills: List[str]) -> int:
        """Compute context tokens saved by JIT-mounting only active skills vs full catalog."""
        total_weight = sum(spec["token_weight"] for spec in self.SKILL_INDEX.values())
        mounted_weight = sum(
            self.SKILL_INDEX[s]["token_weight"]
            for s in mounted_skills
            if s in self.SKILL_INDEX
        )
        return max(0, total_weight - mounted_weight)

    @property
    def mounted_skills(self) -> List[str]:
        return list(self._mounted_skills)
