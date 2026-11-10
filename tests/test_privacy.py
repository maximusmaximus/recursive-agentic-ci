import unittest
from src.core.privacy import VenicePrivacyProxy


class TestVenicePrivacy(unittest.TestCase):
    def setUp(self):
        self.privacy = VenicePrivacyProxy()

    def test_secret_scrubbing(self):
        dirty_code = (
            "api_key = 'sk-1234567890abcdef1234567890abcdef'\n"
            "token = 'ghp_abcdef1234567890abcdef1234567890'\n"
            "poa_key = 'pk_live_9876543210abcdef987654'\n"
            "session_key = 'psk_session_1234567890abcdef'\n"
            "venice_key = 'vv_ak_1234567890abcdef123456'\n"
            "auth_header = 'Bearer 2u6GZL1hOE_3TPrByRzdndMsxwUGwJF3lYDbm6HEzME'\n"
            "pem = '''-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC\n-----END PRIVATE KEY-----'''\n"
            "user_email = 'admin@internal-corp.com'\n"
            "internal_ip = '192.168.1.100'\n"
        )
        clean = self.privacy.sanitize_code_payload(dirty_code)

        self.assertNotIn("sk-1234567890abcdef", clean)
        self.assertNotIn("ghp_abcdef1234567890", clean)
        self.assertNotIn("pk_live_9876543210abcdef987654", clean)
        self.assertNotIn("psk_session_1234567890abcdef", clean)
        self.assertNotIn("vv_ak_1234567890abcdef123456", clean)
        self.assertNotIn("2u6GZL1hOE_3TPrByRzdndMsxwUGwJF3lYDbm6HEzME", clean)
        self.assertNotIn("MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC", clean)
        self.assertNotIn("admin@internal-corp.com", clean)
        self.assertNotIn("192.168.1.100", clean)

        self.assertIn("[REDACTED_OPENAI_TOKEN]", clean)
        self.assertIn("[REDACTED_GITHUB_TOKEN]", clean)
        self.assertIn("[REDACTED_POA_SECRET_KEY]", clean)
        self.assertIn("[REDACTED_POA_SESSION_KEY]", clean)
        self.assertIn("[REDACTED_VENICE_KEY]", clean)
        self.assertIn("Bearer [REDACTED_BEARER_TOKEN]", clean)
        self.assertIn("[REDACTED_PRIVATE_KEY_PEM]", clean)
        self.assertIn("[REDACTED_EMAIL]", clean)
        self.assertIn("[REDACTED_IP]", clean)

    def test_e2ee_enclave_model_resolution(self):
        zdr_proxy = VenicePrivacyProxy(model="deepseek-r1", e2ee_enabled=False)
        self.assertEqual(zdr_proxy.resolve_model(), "deepseek-r1")

        e2ee_proxy = VenicePrivacyProxy(model="deepseek-r1", e2ee_enabled=True)
        self.assertEqual(e2ee_proxy.resolve_model(), "e2ee-deepseek-v4-flash")
        self.assertEqual(e2ee_proxy.resolve_model("llama-3.3-70b"), "e2ee-kimi-k3-p")
        self.assertEqual(e2ee_proxy.resolve_model("e2ee-custom-model"), "e2ee-custom-model")

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
        self.assertEqual(abstract["privacy_mode"], "venice_zdr")
        self.assertTrue(any("class Engine:" in iface for iface in abstract["interfaces"]))
        self.assertNotIn("ghp_abcdef", abstract["safe_excerpt"])

    def test_plan_improvement_offline(self):
        e2ee_proxy = VenicePrivacyProxy(model="llama-3.3-70b", e2ee_enabled=True)
        vec = {
            "type": "feature",
            "module": "calculator.py",
            "target": "Calculator",
            "title": "Add factorize method",
            "category": "algorithmic_expansion",
        }
        plan = e2ee_proxy.plan_improvement({}, vec, maintainer_rules=["DO NOT: use third-party math"])
        self.assertIn("title", plan)
        self.assertIn("rationale", plan)
        self.assertIn("affected_files", plan)
        self.assertEqual(plan["privacy_model"], "e2ee-kimi-k3-p")
        self.assertGreaterEqual(plan["safety_score"], 0.8)


if __name__ == "__main__":
    unittest.main()
