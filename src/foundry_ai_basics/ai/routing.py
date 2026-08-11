from __future__ import annotations

import json
import time

from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from openai import OpenAI

from foundry_ai_basics.ai.mcp import MCPToolClient
from foundry_ai_basics.config import (
    IntentClassifierConfig,
    RoutedModelConfig,
    RoutingConfig,
)

from foundry_ai_basics.ai.tools import execute_tool_with_retry

if TYPE_CHECKING:
    from foundry_ai_basics.open_telemetry import OpenTelemetry


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
    mcp_client: MCPToolClient | None = None,
    open_telemetry_client: OpenTelemetry | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> RoutingResult:
    """
    Route question to appropriate model based on intent classification.
    """

    with _trace_span(
        open_telemetry_client,
        "routing.route_to_model",
        attributes={"routing.message_count": len(messages)},
    ) as route_span:
        print(
            f"\n[INTENT CLASSIFIER]: Using SLM ({routing.slm.deployment_name}) for classification..."
        )
        with _trace_span(
            open_telemetry_client,
            "routing.classify_intent",
            attributes={"model.name": routing.slm.deployment_name},
        ):
            intent = classify_intent_via_slm(
                client,
                user_question,
                routing.slm.deployment_name,
                routing.intent_classifier,
            )

        print(f"[INTENT CLASSIFIER]: Question classified as: {intent.upper()}")

        selected_model = _select_model(intent, routing)
        _print_routing_decision(selected_model)

        if route_span:
            route_span.set_attribute("routing.intent", intent)
            route_span.set_attribute("model.name", selected_model.deployment_name)
            route_span.set_attribute("model.type", selected_model.model_type)

        messages = messages[-selected_model.max_past_messages :]

        start_time = time.time()

        request_args: dict[str, Any] = {
            "model": selected_model.deployment_name,
            "messages": messages,
            "max_completion_tokens": selected_model.max_tokens,
            "temperature": selected_model.temperature,
            "top_p": selected_model.top_p,
        }

        if mcp_client:
            with _trace_span(open_telemetry_client, "mcp.list_tools"):
                tools = mcp_client.list_tools()

        if tools:
            request_args["tools"] = tools

        with _trace_span(
            open_telemetry_client,
            "llm.chat_completion",
            attributes={"model.name": selected_model.deployment_name},
        ):
            response = client.chat.completions.create(**request_args)

        latency_ms = (time.time() - start_time) * 1000
        message = response.choices[0].message
        reply = message.content

        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            tool_count = len(tool_calls)
            print(f"\n[TOOL CALLING] LLM requested {tool_count} tool call(s)")

            if route_span:
                route_span.set_attribute("tool.call_count", tool_count)

            messages.append(_assistant_message_with_tool_calls(message))

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_arguments = json.loads(tool_call.function.arguments)
                tool_call_id = tool_call.id

                with _trace_span(
                    open_telemetry_client,
                    "mcp.call_tool",
                    attributes={"tool.name": tool_name},
                ):
                    if mcp_client:
                        tool_result = mcp_client.execute_tool_with_retry(
                            tool_name,
                            tool_arguments,
                        )
                    else:
                        tool_result = execute_tool_with_retry(
                            tool_name,
                            tool_arguments,
                        )

                tool_response = {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": tool_result,
                }
                messages.append(tool_response)

            print("\n[LLM CALL] Sending tool results back to LLM for final answer...")
            with _trace_span(
                open_telemetry_client,
                "llm.final_response",
                attributes={"model.name": selected_model.deployment_name},
            ):
                second_response = client.chat.completions.create(
                    model=selected_model.deployment_name,
                    messages=messages,
                    max_completion_tokens=selected_model.max_tokens,
                    temperature=selected_model.temperature,
                    top_p=selected_model.top_p,
                )
            response = second_response
            reply = second_response.choices[0].message.content

        token_usage = _extract_token_usage(response)
        if route_span and token_usage:
            route_span.set_attribute("tokens.prompt", token_usage["prompt_tokens"])
            route_span.set_attribute(
                "tokens.completion",
                token_usage["completion_tokens"],
            )
            route_span.set_attribute("tokens.total", token_usage["total_tokens"])

        return RoutingResult(
            reply=reply,
            model_name=selected_model.deployment_name,
            model_type=selected_model.model_type,
            intent=intent,
            latency_ms=latency_ms,
            token_usage=token_usage,
        )


def _assistant_message_with_tool_calls(message: Any) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": message.content,
        "tool_calls": [
            tool_call.model_dump(exclude_none=True) for tool_call in message.tool_calls
        ],
    }


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


def _trace_span(
    open_telemetry_client: OpenTelemetry | None,
    name: str,
    attributes: dict[str, Any] | None = None,
):
    if not open_telemetry_client:
        return nullcontext(None)

    return open_telemetry_client.create_span(
        name,
        attributes=attributes,
    )
