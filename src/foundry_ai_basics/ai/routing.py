import time
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from foundry_ai_basics.config import (
    IntentClassifierConfig,
    RoutedModelConfig,
    RoutingConfig,
)


@dataclass(frozen=True)
class RoutingResult:
    reply: str | None
    model_name: str
    model_type: str
    intent: str
    latency_ms: float
    token_usage: dict[str, int] | None


def classify_intent_via_slm(
    client: OpenAI,
    user_question: str,
    deployment_name: str,
    config: IntentClassifierConfig,
) -> str:
    system_instruction = """
    You classify questions or user prompts as either "simple" or "complex":

    A "simple" question is a straightforward query that can be answered with a fact, definition, or short response. Examples include greetings, basic facts, and simple instructions.

    A "complex" question requires deeper reasoning, analysis, comparison, planning, or multi-step thinking. Examples include "compare product A and B", "what if scenarios", and "recommend a strategy".

    Respond with only one word: "simple" or "complex".
    """

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_question},
    ]

    response = client.chat.completions.create(
        model=deployment_name,
        messages=messages,
        max_completion_tokens=config.max_tokens,
        temperature=config.temperature,
        top_p=config.top_p,
    )

    classification = response.choices[0].message.content.strip().lower()
    if classification not in ["simple", "complex"]:
        print(
            f"[INTENT CLASSIFIER]: Unexpected classification result: '{classification}'. Defaulting to 'complex'."
        )
        return "complex"

    return classification


def route_to_model(
    client: OpenAI,
    user_question: str,
    routing: RoutingConfig,
    messages: list[dict[str, str]],
) -> RoutingResult:
    """
    Route question to appropriate model based on intent classification.
    """

    print(
        f"\n[INTENT CLASSIFIER]: Using SLM ({routing.slm.deployment_name}) for classification..."
    )
    intent = classify_intent_via_slm(
        client,
        user_question,
        routing.slm.deployment_name,
        routing.intent_classifier,
    )

    print(f"[INTENT CLASSIFIER]: Question classified as: {intent.upper()}")

    selected_model = _select_model(intent, routing)
    _print_routing_decision(selected_model)

    messages = messages[
        -selected_model.max_past_messages:
    ]  # Keep only the most recent messages within the limit

    start_time = time.time()

    response = client.chat.completions.create(
        model=selected_model.deployment_name,
        messages=messages,
        max_completion_tokens=selected_model.max_tokens,
        temperature=selected_model.temperature,
        top_p=selected_model.top_p,
    )

    latency_ms = (time.time() - start_time) * 1000
    reply = response.choices[0].message.content

    return RoutingResult(
        reply=reply,
        model_name=selected_model.deployment_name,
        model_type=selected_model.model_type,
        intent=intent,
        latency_ms=latency_ms,
        token_usage=_extract_token_usage(response),
    )


def _select_model(intent: str, routing: RoutingConfig) -> RoutedModelConfig:
    if intent == "simple":
        return routing.slm

    return routing.llm


def _print_routing_decision(model: RoutedModelConfig) -> None:
    if model.model_type == "SLM":
        print(f"[ROUTING]: Sending to ({model.deployment_name}) - faster and cheaper")
        return

    print(
        f"[ROUTING]: Sending to ({model.deployment_name}) - more capable for complex tasks"
    )


def _extract_token_usage(response: Any) -> dict[str, int] | None:
    if not hasattr(response, "usage") or not response.usage:
        return None

    return {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }
