import io
import unittest
from contextlib import redirect_stdout

from foundry_ai_basics.ai.routing import route_to_model
from foundry_ai_basics.config import (
    IntentClassifierConfig,
    RoutedModelConfig,
    RoutingConfig,
)


class FakeUsage:
    prompt_tokens = 10
    completion_tokens = 4
    total_tokens = 14


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeMessage(content)


class FakeResponse:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]
        self.usage = FakeUsage()


class FakeCompletions:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


class FakeChat:
    def __init__(self, responses):
        self.completions = FakeCompletions(responses)


class FakeOpenAIClient:
    def __init__(self, responses):
        self.chat = FakeChat(responses)


class RoutingTests(unittest.TestCase):
    def test_route_to_model_uses_slm_settings_for_simple_intent(self):
        client = FakeOpenAIClient([FakeResponse("simple"), FakeResponse("Hi there")])
        routing = _routing_config()

        result = _route_quietly(
            client,
            user_question="Hello",
            routing=routing,
            messages=_messages(),
        )

        classifier_call, routed_call = client.chat.completions.calls
        self.assertEqual(classifier_call["model"], "phi-4")
        self.assertEqual(classifier_call["max_completion_tokens"], 5)
        self.assertEqual(routed_call["model"], "phi-4")
        self.assertEqual(routed_call["max_completion_tokens"], 100)
        self.assertEqual(routed_call["temperature"], 0.25)
        self.assertEqual(result.model_type, "SLM")
        self.assertEqual(
            result.token_usage,
            {
                "prompt_tokens": 10,
                "completion_tokens": 4,
                "total_tokens": 14,
            },
        )

    def test_route_to_model_uses_llm_settings_for_complex_intent(self):
        client = FakeOpenAIClient([FakeResponse("complex"), FakeResponse("Analysis")])
        routing = _routing_config()

        result = _route_quietly(
            client,
            user_question="Compare two return strategies",
            routing=routing,
            messages=_messages(),
        )

        routed_call = client.chat.completions.calls[1]
        self.assertEqual(routed_call["model"], "gpt-4.1-mini")
        self.assertEqual(routed_call["max_completion_tokens"], 150)
        self.assertEqual(routed_call["temperature"], 0.5)
        self.assertEqual(result.model_type, "LLM")


def _routing_config():
    return RoutingConfig(
        intent_classifier=IntentClassifierConfig(
            max_tokens=5,
            temperature=0,
            top_p=1.0,
        ),
        llm=RoutedModelConfig(
            deployment_name="gpt-4.1-mini",
            model_type="LLM",
            max_past_messages=10,
            max_tokens=150,
            temperature=0.5,
            top_p=0.5,
        ),
        slm=RoutedModelConfig(
            deployment_name="phi-4",
            model_type="SLM",
            max_past_messages=5,
            max_tokens=100,
            temperature=0.25,
            top_p=0.25,
        ),
    )


def _messages():
    return [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello"},
    ]


def _route_quietly(client, user_question, routing, messages):
    with redirect_stdout(io.StringIO()):
        return route_to_model(
            client,
            user_question=user_question,
            routing=routing,
            messages=messages,
        )


if __name__ == "__main__":
    unittest.main()
