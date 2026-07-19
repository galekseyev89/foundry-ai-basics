import time
from dataclasses import dataclass
from typing import Any

from openai import OpenAI


@dataclass(frozen=True)
class RoutingResult:
    reply: str | None
    model_label: str
    model_type: str
    intent: str
    latency_ms: float
    token_usage: dict[str, int] | None


def classify_intent(user_question: str) -> str:
    question_lower = user_question.lower()

    complex_patterns = [
        "compare",
        "contrast",
        "analyze",
        "evaluate",
        "why should",
        "what if",
        "how would",
        "plan",
        "strategy",
        "recommend",
        "suggest",
    ]

    for pattern in complex_patterns:
        if pattern in question_lower:
            return "complex"

    simple_patterns = [
        "hello",
        "hi",
        "hey",
        "greetings",
        "what is",
        "who is",
        "when is",
        "where is",
        "how are you",
        "thanks",
        "thank you",
    ]

    for pattern in simple_patterns:
        if pattern in question_lower:
            return "simple"

    if len(user_question.split()) > 20:
        return "complex"

    return "simple"


def classify_intent_via_slm(
    client: OpenAI,
    user_question: str,
    slm_deployment_name: str,
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
        model=slm_deployment_name,
        messages=messages,
    )

    classification = response.choices[0].message.content.strip().lower()
    if classification not in ["simple", "complex"]:
        print(
            f"Unexpected classification result: '{classification}'. "
            "Defaulting to 'complex'."
        )
        return "complex"

    return classification


def route_to_model(
    client: OpenAI,
    user_question: str,
    messages: list[dict[str, str]],
    llm_deployment_name: str,
    slm_deployment_name: str,
    use_slm_classifier: bool = True,
) -> RoutingResult:
    if use_slm_classifier:
        print("\n[INTENT CLASSIFIER] Using SLM (Phi-4) for classification...")
        intent = classify_intent_via_slm(client, user_question, slm_deployment_name)
    else:
        print("\n[INTENT CLASSIFIER] Using keyword-based classification...")
        intent = classify_intent(user_question)

    print(f"\n[INTENT CLASSIFIER] Question classified as: {intent.upper()}")

    if intent == "simple":
        print("[ROUTING] Sending to Phi-4 (SLM) - faster and cheaper")
        model_label = "Phi-4 (SLM)"
        model_type = "SLM"
        deployment = slm_deployment_name
    else:
        print(
            "[ROUTING] Sending to GPT-4.1-Mini (LLM) - "
            "more capable for complex tasks"
        )
        model_label = "GPT-4.1-Mini (LLM)"
        model_type = "LLM"
        deployment = llm_deployment_name

    start_time = time.time()

    response = client.chat.completions.create(model=deployment, messages=messages)

    latency_ms = (time.time() - start_time) * 1000
    reply = response.choices[0].message.content

    return RoutingResult(
        reply=reply,
        model_label=model_label,
        model_type=model_type,
        intent=intent,
        latency_ms=latency_ms,
        token_usage=_extract_token_usage(response),
    )


def _extract_token_usage(response: Any) -> dict[str, int] | None:
    if not hasattr(response, "usage") or not response.usage:
        return None

    return {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }
