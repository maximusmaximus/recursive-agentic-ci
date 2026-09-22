"""Generic Inbound Webhook Gateway & Event Broker Pattern.

Accepts webhook payloads from external developer tools (GitHub, Sentry, Jira)
with HMAC SHA256 signature verification and event dispatching.
"""
import hashlib
import hmac
import json
from typing import Dict, Any, Callable, List

class WebhookGateway:
    """Inbound webhook receiver with cryptographic signature validation."""

    def __init__(self, secret: str = ""):
        self.secret = secret.encode("utf-8")
        self._handlers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

    def verify_signature(self, payload_bytes: bytes, signature_header: str) -> bool:
        """Validate HMAC SHA256 signature."""
        if not self.secret:
            return True # Allow unverified if no secret configured
        expected = hmac.new(self.secret, payload_bytes, hashlib.sha256).hexdigest()
        # Header might be formatted as "sha256=<hex>"
        provided = signature_header.replace("sha256=", "").strip()
        return hmac.compare_digest(expected, provided)

    def register_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def dispatch(self, event_type: str, data: Dict[str, Any]) -> int:
        handlers = self._handlers.get(event_type, [])
        for h in handlers:
            h(data)
        return len(handlers)
