"""In-memory data store with unindexed lookups (performance optimization vector)."""
from typing import Dict, Any, Optional

class MemoryDataStore:
    def __init__(self):
        self._users: Dict[str, dict] = {}
        self._counter = 0

    def add_user(self, user_data: dict) -> str:
        self._counter += 1
        user_id = f"usr_{self._counter}"
        self._users[user_id] = {**user_data, "id": user_id}
        return user_id

    def get_user(self, user_id: str) -> Optional[dict]:
        return self._users.get(user_id)

    def find_by_email(self, email: str) -> Optional[dict]:
        # Unindexed linear scan - performance bottleneck vector
        for user in self._users.values():
            if user.get("email") == email:
                return user
        return None

    def all_users(self):
        return list(self._users.values())
