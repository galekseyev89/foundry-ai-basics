from routing import RoutingResult


def format_reply(reply: str) -> None:
    print("=" * 50)
    print(reply)
    print("\n" + "=" * 50)


def print_performance_metrics(result: RoutingResult) -> None:
    print("\n" + "=" * 50)
    print("PERFORMANCE METRICS:")
    print("=" * 50)
    print(f"Model used: {result.model_label}")
    print(f"Latency: {result.latency_ms:.2f} ms")

    if not result.token_usage:
        return

    print(f"Prompt tokens: {result.token_usage['prompt_tokens']}")
    print(f"Completion tokens: {result.token_usage['completion_tokens']}")
    print(f"Total tokens: {result.token_usage['total_tokens']}")

    if result.model_type == "SLM":
        estimated_cost = result.token_usage["total_tokens"] * 0.0000002
        print(f"Estimated cost: ${estimated_cost:.6f} (SLM rates)")
    else:
        estimated_cost = result.token_usage["total_tokens"] * 0.00001
        print(f"Estimated cost: ${estimated_cost:.6f} (LLM rates)")


def print_routing_explanation(result: RoutingResult) -> None:
    print("\n" + "=" * 50)
    print("ROUTING DECISION EXPLANATION:")
    print("=" * 50)

    if result.intent == "simple":
        print("Question classified as SIMPLE -> Routed to Phi-4 (faster, cheaper)")
        print("Examples: greetings, basic facts, short answers")
    else:
        print("Question classified as COMPLEX -> Routed to GPT-4.1-Mini (more capable)")
        print("Examples: analysis, comparison, planning, multi-step reasoning")
