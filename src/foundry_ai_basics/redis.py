from __future__ import annotations

import json
import time
from typing import Any

from foundry_ai_basics.config import RedisConfig


class RedisMemory:
    """Stores short-lived session memory in Redis, with an in-memory fallback."""

    def __init__(
        self,
        redis_client,
        config: RedisConfig,
    ) -> None:
        self.redis_client = redis_client
        self.ttl_seconds = config.session_ttl_seconds
        self.max_messages_in_history = config.max_messages_in_history
        self.in_memory_cache: dict[str, dict[str, Any]] = {}

    def save_conversation(
        self,
        session_id: str,
        messages: list[dict[str, str]],
    ) -> None:
        """Save the latest conversation messages for a session."""
        trimmed_messages = messages[-self.max_messages_in_history :]
        self._save_json(self._get_key(session_id, "messages"), trimmed_messages)

    def load_conversation(self, session_id: str) -> list[dict[str, str]]:
        """Load conversation messages for a session."""
        return self._load_json(self._get_key(session_id, "messages"), default=[])

    def save_state(self, session_id: str, state: dict[str, Any]) -> None:
        """Save session state such as pending approval or tool state."""
        self._save_json(self._get_key(session_id, "state"), state)

    def load_state(self, session_id: str) -> dict[str, Any]:
        """Load state for a session."""
        return self._load_json(self._get_key(session_id, "state"), default={})

    def refresh_ttl(self, session_id: str) -> None:
        """Refresh expiration time for all session data."""
        for key_type in ["messages", "state"]:
            key = self._get_key(session_id, key_type)
            if self.redis_client:
                self.redis_client.expire(key, self.ttl_seconds)
            elif key in self.in_memory_cache:
                self.in_memory_cache[key]["expires_at"] = self._expires_at()

    def clear_session(self, session_id: str) -> None:
        """Clear all memory for a session."""
        for key_type in ["messages", "state"]:
            key = self._get_key(session_id, key_type)
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                self.in_memory_cache.pop(key, None)

    def _save_json(self, key: str, value: Any) -> None:
        data = json.dumps(value)

        if self.redis_client:
            self.redis_client.setex(key, self.ttl_seconds, data)
            return

        self.in_memory_cache[key] = {
            "data": data,
            "expires_at": self._expires_at(),
        }

    def _load_json(self, key: str, default: Any) -> Any:
        if self.redis_client:
            data = self.redis_client.get(key)
            if data is None:
                return default
            return json.loads(_decode_redis_value(data))

        cached = self.in_memory_cache.get(key)
        if not cached:
            return default

        if cached["expires_at"] <= time.time():
            self.in_memory_cache.pop(key, None)
            return default

        return json.loads(cached["data"])

    def _expires_at(self) -> float:
        return time.time() + self.ttl_seconds

    @staticmethod
    def _get_key(session_id: str, key_type: str) -> str:
        return f"session:{session_id}:{key_type}"


def _decode_redis_value(data: bytes | str) -> str:
    if isinstance(data, bytes):
        return data.decode("utf-8")

    return data
