"""Telegram Bot Runner.

Manages the long-polling loop against the Telegram Bot API,
dispatching incoming messages and callback queries to handlers.
"""
import json
import os
import time
import urllib.request
from typing import Optional, Dict, Any
from .handlers import TelegramBotHandlers
from ..hermes.agent import HermesCIAgent

class TelegramHITLBot:
    """Telegram bot instance polling for maintainer interactions."""

    def __init__(self, token: Optional[str] = None, agent: Optional[HermesCIAgent] = None):
        self.token = token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.agent = agent or HermesCIAgent()
        self.handlers = TelegramBotHandlers(self.agent)
        self.base_url = f"https://api.telegram.org/bot{self.token}" if self.token else ""
        self._last_update_id = 0
        self._running = False

    def send_message(self, chat_id: str, text: str, reply_markup: Optional[Dict[str, Any]] = None) -> bool:
        """Send a message to a Telegram chat with optional inline keyboard."""
        if not self.token:
            print(f"[Telegram Mock] To: {chat_id}\n{text}\nMarkup: {reply_markup}\n")
            return True

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": reply_markup or {}
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"[Telegram Error] send_message failed: {e}")
            return False

    def answer_callback_query(self, callback_query_id: str, text: Optional[str] = None):
        if not self.token:
            return
        url = f"{self.base_url}/answerCallbackQuery"
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass

    def poll_once(self):
        """Fetch and process new updates from Telegram."""
        if not self.token:
            return

        url = f"{self.base_url}/getUpdates?offset={self._last_update_id + 1}&timeout=10"
        try:
            req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                updates = data.get("result", [])

                for update in updates:
                    self._last_update_id = update["update_id"]
                    self._process_update(update)
        except Exception as e:
            print(f"[Telegram Polling Error]: {e}")

    def _process_update(self, update: Dict[str, Any]):
        # Handle Callback Query (Button clicks)
        if "callback_query" in update:
            cb = update["callback_query"]
            cb_id = cb["id"]
            user_id = str(cb["from"]["id"])
            chat_id = str(cb["message"]["chat"]["id"])
            data = cb.get("data", "")

            self.answer_callback_query(cb_id)
            resp_text, kb = self.handlers.handle_callback_query(user_id, data)
            self.send_message(chat_id, resp_text, kb)

        # Handle Slash Command or Text Message
        elif "message" in update and "text" in update["message"]:
            msg = update["message"]
            text = msg["text"].strip()
            chat_id = str(msg["chat"]["id"])
            user_id = str(msg["from"]["id"])

            if text.startswith("/"):
                parts = text.split(" ", 1)
                cmd = parts[0]
                args = parts[1] if len(parts) > 1 else ""
                resp_text, kb = self.handlers.handle_command(user_id, cmd, args)
                self.send_message(chat_id, resp_text, kb)
            else:
                resp_text, kb = self.handlers.handle_text_message(user_id, text)
                self.send_message(chat_id, resp_text, kb)

    def start_polling(self):
        """Continuous polling loop."""
        print("[*] Starting Telegram HITL Bot polling...")
        self._running = True
        while self._running:
            try:
                self.poll_once()
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[Telegram Bot Exception]: {e}")
                time.sleep(2)
