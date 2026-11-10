"""Resource Governor and Budget Tracking.

Monitors active worker processes, token burn rates, memory constraints,
and disk footprint to ensure the agent does not overwhelm host resources.
"""
import os
import shutil
import time
from typing import Dict, Any, Optional

class ResourceGovernor:
    """Tracks and throttles system and LLM token resources."""

    def __init__(
        self,
        daily_token_quota: int = 250000,
        max_concurrent_sandboxes: int = 2,
        state_manager: Optional[Any] = None,
    ):
        self.daily_token_quota = daily_token_quota
        self.max_concurrent_sandboxes = max_concurrent_sandboxes
        self._state_manager = state_manager
        self._tokens_consumed_today = 0
        self._context_tokens_saved = 0
        self._active_sandboxes = 0
        self._last_reset = time.time()

    def check_sandbox_capacity(self) -> bool:
        return self._active_sandboxes < self.max_concurrent_sandboxes

    def acquire_sandbox(self) -> bool:
        if self._active_sandboxes < self.max_concurrent_sandboxes:
            self._active_sandboxes += 1
            return True
        return False

    def release_sandbox(self):
        self._active_sandboxes = max(0, self._active_sandboxes - 1)

    def record_tokens(self, count: int):
        self._tokens_consumed_today += count

    def record_context_savings(self, tokens_saved: int):
        self._context_tokens_saved += max(0, int(tokens_saved))

    def get_resource_snapshot(self) -> Dict[str, Any]:
        """Return system and quota telemetry."""
        # Disk usage of data dir
        disk_free_gb = 0.0
        try:
            total, used, free = shutil.disk_usage(".")
            disk_free_gb = round(free / (1024 ** 3), 2)
        except Exception:
            pass

        persisted_tokens = (
            self._state_manager.get_total_tokens_today()
            if self._state_manager is not None
            else 0
        )
        consumed_today = persisted_tokens + self._tokens_consumed_today

        return {
            "daily_token_quota": self.daily_token_quota,
            "tokens_consumed_today": consumed_today,
            "token_budget_remaining": max(0, self.daily_token_quota - consumed_today),
            "quota_utilization_pct": round((consumed_today / max(1, self.daily_token_quota)) * 100, 1),
            "context_tokens_saved": self._context_tokens_saved,
            "active_sandboxes": self._active_sandboxes,
            "max_concurrent_sandboxes": self.max_concurrent_sandboxes,
            "disk_free_gb": disk_free_gb,
            "timestamp": time.time()
        }
