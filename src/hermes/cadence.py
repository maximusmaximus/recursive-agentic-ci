"""Cadence & Cron Scheduler for Periodic Feature Dashes and Snooze Waking.

Coordinates periodic autonomous repository sprints ("Dashes") and checks
for snoozed proposals ready for re-review.
"""
import threading
import time
from typing import Callable, List, Optional, Dict, Any

class CadenceScheduler:
    """Manages periodic execution of feature dashes and snooze awakening."""

    def __init__(self, check_interval_seconds: int = 60):
        self.check_interval_seconds = check_interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._dash_callbacks: List[Callable[[], None]] = []
        self._snooze_wake_callbacks: List[Callable[[List[Dict[str, Any]]], None]] = []

    def on_feature_dash(self, callback: Callable[[], None]):
        self._dash_callbacks.append(callback)

    def on_snooze_wake(self, callback: Callable[[List[Dict[str, Any]]], None]):
        self._snooze_wake_callbacks.append(callback)

    def start(self):
        """Start background scheduler loop."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def _loop(self):
        while self._running:
            try:
                # Trigger registered callbacks
                for cb in self._dash_callbacks:
                    cb()
            except Exception as e:
                print(f"[CadenceScheduler] Error in cadence loop: {e}")
            time.sleep(self.check_interval_seconds)
