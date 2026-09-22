import unittest
try:
    from app import SampleServiceApp
except ImportError:
    from examples.sample_forked_repo.app import SampleServiceApp

class TestSampleApp(unittest.TestCase):
    def setUp(self):
        self.app = SampleServiceApp()

    def test_calc_endpoint(self):
        resp = self.app.handle_request("/api/calc", {"operation": "add", "a": 10, "b": 15})
        self.assertEqual(resp["status"], "success")
        self.assertEqual(resp["result"], 25)

    def test_user_management(self):
        resp = self.app.handle_request("/api/users", {
            "action": "add",
            "user": {"name": "Alice", "email": "alice@example.com"}
        })
        self.assertEqual(resp["status"], "success")
        uid = resp["user_id"]

        get_resp = self.app.handle_request("/api/users", {
            "action": "get",
            "user_id": uid
        })
        self.assertEqual(get_resp["status"], "success")
        self.assertEqual(get_resp["user"]["name"], "Alice")

if __name__ == "__main__":
    unittest.main()
