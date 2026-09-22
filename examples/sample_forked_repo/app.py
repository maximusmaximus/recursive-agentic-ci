"""Sample microservice target repository."""
try:
    from .calculator import Calculator
    from .data_store import MemoryDataStore
except (ImportError, ValueError):
    from calculator import Calculator
    from data_store import MemoryDataStore

class SampleServiceApp:
    def __init__(self):
        self.calc = Calculator()
        self.store = MemoryDataStore()

    def handle_request(self, endpoint: str, payload: dict) -> dict:
        if endpoint == "/api/calc":
            op = payload.get("operation")
            a = payload.get("a", 0)
            b = payload.get("b", 0)
            res = self.calc.compute(op, a, b)
            return {"status": "success", "result": res}
        elif endpoint == "/api/users":
            action = payload.get("action")
            if action == "add":
                uid = self.store.add_user(payload.get("user"))
                return {"status": "success", "user_id": uid}
            elif action == "get":
                user = self.store.get_user(payload.get("user_id"))
                return {"status": "success", "user": user}
            elif action == "find_by_email":
                user = self.store.find_by_email(payload.get("email"))
                return {"status": "success", "user": user}
        return {"status": "error", "message": "Unknown endpoint"}
