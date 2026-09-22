import unittest
from src.patterns.telemetry import TelemetryIngestor
from src.patterns.profiler import PerformanceProfiler
from src.patterns.preferences import MaintainerPreferences
from src.patterns.webhooks import WebhookGateway
from src.patterns.rbac import RBACManager, Role, Permission

class TestPatternedModules(unittest.TestCase):
    def test_telemetry_crash_ingest(self):
        ingestor = TelemetryIngestor()
        trace = (
            "Traceback (most recent call last):\n"
            "  File \"app.py\", line 15, in handle_request\n"
            "  File \"calculator.py\", line 15, in compute\n"
            "ZeroDivisionError: division by zero"
        )
        entry = ingestor.ingest_raw_stacktrace(trace, "ZeroDivisionError")
        self.assertEqual(entry["module"], "calculator.py")
        self.assertEqual(entry["function"], "compute")
        self.assertEqual(entry["line_number"], 15)

        priority = ingestor.get_priority_crashes(limit=1)
        self.assertEqual(len(priority), 1)
        self.assertEqual(priority[0]["function"], "compute")

    def test_profiler_bottlenecks(self):
        profiler = PerformanceProfiler(latency_p95_ms=200.0)
        profiler.ingest_metric({
            "endpoint": "/api/users/search",
            "p95_latency_ms": 450.0,
            "bottleneck_reason": "Missing index on username"
        })
        profiler.ingest_metric({
            "endpoint": "/health",
            "p95_latency_ms": 5.0
        })

        bottlenecks = profiler.get_bottlenecks()
        self.assertEqual(len(bottlenecks), 1)
        self.assertEqual(bottlenecks[0]["endpoint"], "/api/users/search")

    def test_maintainer_preferences(self):
        prefs = MaintainerPreferences()
        prefs.record_feedback("prop-1", approved=False, rationale="Do not use regex for HTML parsing")
        prefs.record_feedback("prop-2", approved=True, rationale="Prefer explicit dataclasses")

        constraints = prefs.get_active_constraints()
        self.assertTrue(any("DO NOT:" in c and "regex" in c for c in constraints))
        self.assertTrue(any("PREFER:" in c and "dataclasses" in c for c in constraints))

    def test_webhook_hmac_verification(self):
        secret = "test_secret_key"
        gateway = WebhookGateway(secret=secret)

        payload = b'{"event": "push", "ref": "refs/heads/main"}'
        import hmac, hashlib
        sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

        self.assertTrue(gateway.verify_signature(payload, f"sha256={sig}"))
        self.assertFalse(gateway.verify_signature(payload, "sha256=invalid_signature"))

    def test_rbac_permissions(self):
        rbac = RBACManager()
        rbac.assign_role("alice", Role.DEVELOPER)
        rbac.assign_role("bob", Role.MAINTAINER)

        self.assertTrue(rbac.is_authorized("alice", Permission.REQUEST_DASH))
        self.assertFalse(rbac.is_authorized("alice", Permission.APPROVE_PROPOSAL))

        self.assertTrue(rbac.is_authorized("bob", Permission.APPROVE_PROPOSAL))
        self.assertTrue(rbac.is_authorized("bob", Permission.TRIGGER_SANDBOX))

if __name__ == "__main__":
    unittest.main()
