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
            config_path.write_text(
                """
                [azure]
                openai_endpoint = "https://file.openai.azure.com"
                llm_deployment_name = "file-llm"
                slm_deployment_name = "file-slm"
                content_safety_endpoint = "https://file.cognitiveservices.azure.com"

                [user]
                name = "Avery"
                role = "learner"

                [safety]
                severity_threshold = 2
                safe_response = "Blocked by test safety policy."

                [prompt]
                max_system_tokens = 3000

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
                """,
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                config = load_config(config_path)

        self.assertEqual(config.azure_openai_endpoint, "https://file.openai.azure.com")
        self.assertEqual(config.llm_deployment_name, "file-llm")
        self.assertEqual(config.slm_deployment_name, "file-slm")
        self.assertEqual(
            config.content_safety_endpoint,
            "https://file.cognitiveservices.azure.com",
        )
        self.assertEqual(config.user_name, "Avery")
        self.assertEqual(config.user_role, "learner")
        self.assertEqual(config.severity_threshold, 2)
        self.assertEqual(config.safe_response, "Blocked by test safety policy.")
        self.assertEqual(config.max_system_tokens, 3000)
        self.assertEqual(config.llm.max_tokens, 200)
        self.assertEqual(config.llm.temperature, 0.5)
        self.assertEqual(config.slm.temperature, 0.1)

    def test_load_config_uses_env_vars_as_overrides(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.toml"
            config_path.write_text(
                """
                [azure]
                openai_endpoint = "https://file.openai.azure.com"
                llm_deployment_name = "file-llm"
                slm_deployment_name = "file-slm"
                content_safety_endpoint = "https://file.cognitiveservices.azure.com"

                [user]
                name = "Avery"
                role = "learner"

                [safety]
                severity_threshold = 2
                safe_response = "Blocked by settings file safety policy."

                [prompt]
                max_system_tokens = 3000

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
                """,
                encoding="utf-8",
            )
            env = {
                "AZURE_OPENAI_ENDPOINT": "https://env.openai.azure.com",
                "LLM_DEPLOYMENT_NAME": "env-llm",
                "SLM_DEPLOYMENT_NAME": "env-slm",
                "CONTENT_SAFETY_ENDPOINT": "https://env.cognitiveservices.azure.com",
                "SAFE_RESPONSE": "Blocked by environment safety policy.",
            }

            with patch.dict(os.environ, env, clear=True):
                config = load_config(config_path)

        self.assertEqual(config.azure_openai_endpoint, "https://env.openai.azure.com")
        self.assertEqual(config.llm_deployment_name, "env-llm")
        self.assertEqual(config.slm_deployment_name, "env-slm")
        self.assertEqual(
            config.content_safety_endpoint,
            "https://env.cognitiveservices.azure.com",
        )
        self.assertEqual(config.safe_response, "Blocked by settings file safety policy.")
        self.assertEqual(config.routing.intent_classifier.max_tokens, 5)
        self.assertEqual(config.routing.llm.deployment_name, "env-llm")
        self.assertEqual(config.routing.llm.model_type, "LLM")
        self.assertEqual(config.routing.llm.max_past_messages, 10)
        self.assertEqual(config.routing.slm.deployment_name, "env-slm")
        self.assertEqual(config.routing.slm.model_type, "SLM")
        self.assertEqual(config.routing.slm.max_past_messages, 5)

    def test_load_config_requires_routing_settings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.toml"
            config_path.write_text(
                """
                [azure]
                openai_endpoint = "https://file.openai.azure.com"
                llm_deployment_name = "file-llm"
                slm_deployment_name = "file-slm"
                content_safety_endpoint = "https://file.cognitiveservices.azure.com"

                [user]
                name = "Avery"
                role = "learner"
                """,
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaisesRegex(ValueError, "safety.severity_threshold"):
                    load_config(config_path)


if __name__ == "__main__":
    unittest.main()
