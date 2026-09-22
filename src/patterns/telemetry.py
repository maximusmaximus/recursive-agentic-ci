"""Runtime Telemetry & Crash Ingestion Pattern.

Normalizes stack traces from Sentry, OpenTelemetry, and runtime crash dumps,
mapping exceptions to repository AST nodes for priority bug-fix sprint generation.
"""
import json
import re
from typing import Dict, List, Any, Optional

class TelemetryIngestor:
    """Ingests and groups runtime crash telemetry."""

    def __init__(self, max_history: int = 200):
        self.max_history = max_history
        self._crashes: List[Dict[str, Any]] = []

    def ingest_payload(self, payload: Dict[str, Any]) -> int:
        """Ingest raw JSON or structured crash dump."""
        crashes_added = 0
        if "crashes" in payload:
            for item in payload["crashes"]:
                self._record_crash(item)
                crashes_added += 1
        elif "stack_trace" in payload or "exception_type" in payload:
            self._record_crash(payload)
            crashes_added += 1
        return crashes_added

    def ingest_raw_stacktrace(self, stack_trace: str, exception_type: str = "UnhandledException") -> Dict[str, Any]:
        """Parse raw stack trace string and identify failing frame."""
        # Find frames: File "path", line X, in func
        frame_matches = re.findall(r'File "([^"]+)", line (\d+), in (\w+)', stack_trace)
        failing_module = "unknown"
        failing_line = 0
        failing_func = "unknown"

        if frame_matches:
            # Pick last frame (deepest in stack)
            failing_module, line_str, failing_func = frame_matches[-1]
            failing_line = int(line_str)

        crash_entry = {
            "exception_type": exception_type,
            "module": failing_module,
            "line_number": failing_line,
            "function": failing_func,
            "stack_trace": stack_trace,
            "frequency": 1
        }
        self._record_crash(crash_entry)
        return crash_entry

    def _record_crash(self, crash: Dict[str, Any]):
        # Deduplicate and increment frequency if matching module and function
        for existing in self._crashes:
            if existing.get("module") == crash.get("module") and existing.get("function") == crash.get("function"):
                existing["frequency"] = existing.get("frequency", 1) + crash.get("frequency", 1)
                return

        self._crashes.append(crash)
        if len(self._crashes) > self.max_history:
            self._crashes.pop(0)

    def get_priority_crashes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Return highest frequency crashes requiring recursive fixes."""
        sorted_crashes = sorted(self._crashes, key=lambda x: x.get("frequency", 1), reverse=True)
        return sorted_crashes[:limit]
