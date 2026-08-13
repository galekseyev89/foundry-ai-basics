import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from foundry_ai_basics.config import load_config


class ConfigTests(unittest.TestCase):
    def test_load_config_reads_settings_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.toml"
            config_path.write_text(_minimal_settings(), encoding="utf-8")
            env = _azure_env()

            with patch.dict(os.environ, env, clear=True):
                config = load_config(config_path)

        self.assertEqual(config.azure_openai_endpoint, "https://env.openai.azure.com")
        self.assertEqual(config.llm_deployment_name, "env-llm")
        self.assertEqual(config.slm_deployment_name, "env-slm")
        self.assertEqual(config.embedding_model_deployment_name, "env-embedding")
        self.assertEqual(
            config.content_safety_endpoint,
            "https://env.cognitiveservices.azure.com",
        )
        self.assertEqual(
            config.search_service_endpoint,
            "https://env.search.windows.net",
        )
        self.assertEqual(config.search_index_name, "foundry-ai-basics-index")
        self.assertEqual(config.user_name, "Avery")
        self.assertEqual(config.user_role, "learner")
        self.assertEqual(config.severity_threshold, 2)
        self.assertEqual(
            config.safe_response, "Blocked by settings file safety policy."
        )
        self.assertEqual(config.max_system_tokens, 3000)
        self.assertEqual(config.redis.host_name, "env-cache.redis.cache.windows.net")
        self.assertEqual(config.redis.access_key, "env-redis-key")
        self.assertEqual(config.redis.port, 6380)
        self.assertEqual(config.redis.session_ttl_seconds, 3600)
        self.assertEqual(config.redis.max_messages_in_history, 20)
        self.assertEqual(config.llm.max_tokens, 200)
        self.assertEqual(config.llm.temperature, 0.5)
        self.assertEqual(config.slm.temperature, 0.1)

    def test_load_config_uses_env_vars_as_overrides(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.toml"
            config_path.write_text(_minimal_settings(), encoding="utf-8")
            env = _azure_env() | {
                "SAFE_RESPONSE": "Blocked by environment safety policy.",
            }

            with patch.dict(os.environ, env, clear=True):
                config = load_config(config_path)

        self.assertEqual(config.azure_openai_endpoint, "https://env.openai.azure.com")
        self.assertEqual(config.llm_deployment_name, "env-llm")
        self.assertEqual(config.slm_deployment_name, "env-slm")
        self.assertEqual(config.embedding_model_deployment_name, "env-embedding")
        self.assertEqual(
            config.content_safety_endpoint,
            "https://env.cognitiveservices.azure.com",
        )
        self.assertEqual(
            config.search_service_endpoint,
            "https://env.search.windows.net",
        )
        self.assertEqual(config.search_index_name, "foundry-ai-basics-index")
        self.assertEqual(
            config.safe_response, "Blocked by settings file safety policy."
        )
        self.assertEqual(config.routing.intent_classifier.max_tokens, 5)
        self.assertEqual(config.routing.llm.deployment_name, "env-llm")
        self.assertEqual(config.routing.llm.model_type, "LLM")
        self.assertEqual(config.routing.llm.max_past_messages, 10)
        self.assertEqual(config.routing.slm.deployment_name, "env-slm")
        self.assertEqual(config.routing.slm.model_type, "SLM")
        self.assertEqual(config.routing.slm.max_past_messages, 5)
        self.assertEqual(config.redis.session_ttl_seconds, 3600)

    def test_load_config_requires_routing_settings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.toml"
            config_path.write_text(
                """
                [user]
                name = "Avery"
                role = "learner"
                """,
                encoding="utf-8",
            )

            with patch.dict(os.environ, _azure_env(), clear=True):
                with self.assertRaisesRegex(ValueError, "safety.severity_threshold"):
                    load_config(config_path)

    def test_load_config_requires_azure_env_vars(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.toml"
            config_path.write_text(_minimal_settings(), encoding="utf-8")

            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(ValueError, "AZURE_OPENAI_ENDPOINT"):
                    load_config(config_path)


def _azure_env():
    return {
        "AZURE_OPENAI_ENDPOINT": "https://env.openai.azure.com",
        "LLM_DEPLOYMENT_NAME": "env-llm",
        "SLM_DEPLOYMENT_NAME": "env-slm",
        "EMBEDDING_MODEL_DEPLOYMENT_NAME": "env-embedding",
        "CONTENT_SAFETY_ENDPOINT": "https://env.cognitiveservices.azure.com",
        "SEARCH_SERVICE_ENDPOINT": "https://env.search.windows.net",
        "APPLICATIONINSIGHTS_CONNECTION_STRING": (
            "InstrumentationKey=00000000-0000-0000-0000-000000000000"
        ),
        "MCP_SERVER_URL": "https://env.example.test/mcp",
        "MCP_API_KEY": "env-mcp-key",
        "REST_API_ENDPOINT": "https://env.example.test/orders",
        "REST_API_KEY": "env-rest-key",
        "EXCHANGE_RATE_API_ENDPOINT": "https://env.example.test/rates",
        "EXCHANGE_RATE_API_KEY": "env-exchange-key",
        "REDIS_HOST_NAME": "env-cache.redis.cache.windows.net",
        "REDIS_ACCESS_KEY": "env-redis-key",
    }


def _minimal_settings():
    return """
    [user]
    name = "Avery"
    role = "learner"

    [safety]
    severity_threshold = 2
    safe_response = "Blocked by settings file safety policy."

    [prompt]
    max_system_tokens = 3000

    [redis]
    session_ttl_seconds = 3600
    max_messages_in_history = 20

    [search]
    index_name = "foundry-ai-basics-index"

    [routing.llm]
    max_past_messages = 10
    max_tokens = 200
    temperature = 0.5
    top_p = 0.5

    [routing.slm]
    max_past_messages = 5
    max_tokens = 100
    temperature = 0.1
    top_p = 0.25

    [routing.intent_classifier]
    max_tokens = 5
    temperature = 0
    top_p = 1.0
    """


if __name__ == "__main__":
    unittest.main()
