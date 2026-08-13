import unittest

from foundry_ai_basics.config import RedisConfig
from foundry_ai_basics.redis import RedisMemory


class FakeRedisClient:
    def __init__(self):
        self.values = {}
        self.ttls = {}
        self.deleted = []

    def setex(self, name, time, value):
        self.values[name] = value.encode("utf-8")
        self.ttls[name] = time

    def get(self, name):
        return self.values.get(name)

    def expire(self, name, time):
        self.ttls[name] = time

    def delete(self, *names):
        self.deleted.extend(names)
        for name in names:
            self.values.pop(name, None)
            self.ttls.pop(name, None)


class RedisMemoryTests(unittest.TestCase):
    def test_save_conversation_trims_history_and_uses_redis_ttl(self):
        redis_client = FakeRedisClient()
        memory = RedisMemory(redis_client, _redis_config(max_messages=2))
        messages = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "second"},
            {"role": "user", "content": "third"},
        ]

        memory.save_conversation("abc", messages)

        self.assertEqual(
            memory.load_conversation("abc"),
            [
                {"role": "assistant", "content": "second"},
                {"role": "user", "content": "third"},
            ],
        )
        self.assertEqual(redis_client.ttls["session:abc:messages"], 60)

    def test_save_state_uses_in_memory_fallback_without_redis_client(self):
        memory = RedisMemory(None, _redis_config())

        memory.save_state("abc", {"awaiting_approval": True})

        self.assertEqual(
            memory.load_state("abc"),
            {"awaiting_approval": True},
        )

    def test_clear_session_removes_conversation_and_state(self):
        memory = RedisMemory(None, _redis_config())
        memory.save_conversation("abc", [{"role": "user", "content": "hello"}])
        memory.save_state("abc", {"pending_tool_call": "lookup_order"})

        memory.clear_session("abc")

        self.assertEqual(memory.load_conversation("abc"), [])
        self.assertEqual(memory.load_state("abc"), {})


def _redis_config(max_messages=5):
    return RedisConfig(
        host_name=None,
        access_key=None,
        port=6380,
        session_ttl_seconds=60,
        max_messages_in_history=max_messages,
    )


if __name__ == "__main__":
    unittest.main()
