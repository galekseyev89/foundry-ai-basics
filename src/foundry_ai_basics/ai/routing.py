import time
from dataclasses import dataclass
from typing import Any

from openai import OpenAI


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
    max_tokens: int,
    temperature: float,
    top_p: float,
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
        max_completion_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
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

    intent_classifier_max_tokens: int,
    intent_classifier_temperature: float,
    intent_classifier_top_p: float,
    
    llm_model_deployment_name: str,
    llm_max_past_messages: int,
    llm_max_tokens: int,
    llm_temperature: float,
    llm_top_p: float,

    slm_model_deployment_name: str,
    slm_max_past_messages: int,
    slm_max_tokens: int,
    slm_temperature: float,
    slm_top_p: float,
    
    messages: list[dict[str, str]]
) -> RoutingResult:
    """
    Route question to appropriate model based on intent classification.
    Returns: (response_text, model_name, latency_ms, token_usage)
    """
  
    print(f"\n[INTENT CLASSIFIER]: Using SLM ({slm_model_deployment_name}) for classification...")
    intent = classify_intent_via_slm(
        client,
        user_question,
        slm_model_deployment_name,
        intent_classifier_max_tokens,
        intent_classifier_temperature,
        intent_classifier_top_p,
    )

    print(f"\n[INTENT CLASSIFIER]: Question classified as: {intent.upper()}")

    if intent == "simple":
        print(f"[ROUTING]: Sending to ({slm_model_deployment_name}) - faster and cheaper")

        model_type = "SLM"
        model_name = slm_model_deployment_name
        max_past_messages = slm_max_past_messages
        max_tokens = slm_max_tokens
        temperature = slm_temperature
        top_p = slm_top_p
    else:
        print(
            f"[ROUTING]: Sending to ({llm_model_deployment_name}) - more capable for complex tasks"
        )
        model_type = "LLM"
        model_name = llm_model_deployment_name
        max_past_messages = llm_max_past_messages
        max_tokens = llm_max_tokens
        temperature = llm_temperature
        top_p = llm_top_p

    messages = messages[
        -max_past_messages:
    ]  # Keep only the most recent messages within the limit

    start_time = time.time()

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_completion_tokens=max_tokens,  # Set the maximum length of the response
        temperature=temperature,  # Control the creativity of the response
        top_p=top_p,  # Control the diversity of the token selection
    )

    latency_ms = (time.time() - start_time) * 1000
    reply = response.choices[0].message.content

    return RoutingResult(
        reply=reply,
        model_name=model_name,
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
