import unittest
from src.core.privacy import VenicePrivacyProxy

class TestVenicePrivacy(unittest.TestCase):
    def setUp(self):
        self.privacy = VenicePrivacyProxy()

    def test_secret_scrubbing(self):
        dirty_code = (
            "api_key = 'sk-1234567890abcdef1234567890abcdef'\n"
            "token = 'ghp_abcdef1234567890abcdef1234567890'\n"
            "user_email = 'admin@internal-corp.com'\n"
            "internal_ip = '192.168.1.100'\n"
        )
        clean = self.privacy.sanitize_code_payload(dirty_code)

        self.assertNotIn("sk-1234567890abcdef", clean)
        self.assertNotIn("ghp_abcdef1234567890", clean)
        self.assertNotIn("admin@internal-corp.com", clean)
        self.assertNotIn("192.168.1.100", clean)
        self.assertIn("[REDACTED_OPENAI_TOKEN]", clean)
        self.assertIn("[REDACTED_EMAIL]", clean)
        self.assertIn("[REDACTED_IP]", clean)

    def test_abstract_ast_context(self):
        code = (
            "import os\n"
            "class Engine:\n"
            "    def start(self, key: str):\n"
            "        secret = 'ghp_abcdef1234567890abcdef1234567890'\n"
            "        return True\n"
        )
        abstract = self.privacy.abstract_ast_context(code, "engine.py")
        self.assertEqual(abstract["path"], "engine.py")
        self.assertTrue(any("class Engine:" in iface for iface in abstract["interfaces"]))
        self.assertNotIn("ghp_abcdef", abstract["safe_excerpt"])

    def test_plan_improvement_offline(self):
        vec = {
            "type": "feature",
            "module": "calculator.py",
            "target": "Calculator",
            "title": "Add factorize method",
            "category": "algorithmic_expansion"
        }
        plan = self.privacy.plan_improvement({}, vec, maintainer_rules=["DO NOT: use third-party math"])
        self.assertIn("title", plan)
        self.assertIn("rationale", plan)
        self.assertIn("affected_files", plan)
        self.assertGreaterEqual(plan["safety_score"], 0.8)

if __name__ == "__main__":
    unittest.main()
