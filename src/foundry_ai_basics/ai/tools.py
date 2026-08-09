import time
import json
import requests

from openai import OpenAI

SAMPLE_REFUND_RECORDS = {
    "12345": {
        "eligible": False,
        "reason": "The TV order is outside the standard 30-day return window.",
        "next_step": (
            "Offer troubleshooting help or escalate if the customer disputes the policy."
        ),
    },
    "54321": {
        "eligible": False,
        "reason": "The mountain bike order is outside the standard 30-day return window.",
        "next_step": "Explain the return window and offer warranty support if relevant.",
    },
    "67890": {
        "eligible": True,
        "reason": "The espresso machine order has a documented product issue exception.",
        "next_step": "Confirm the customer's email address before starting the refund.",
    },
    "24680": {
        "eligible": False,
        "reason": "The yoga mat order is outside the standard 30-day return window.",
        "next_step": "Explain the return window and offer product care guidance.",
    },
}


def get_available_tools():
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_knowledge_base",
                "description": "Search the customer support knowledge base.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The user's product or policy question.",
                        },
                    },
                    "required": ["question"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "check_refund_eligibility",
                "description": "Check whether a customer order is eligible for a refund.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_number": {
                            "type": "string",
                            "description": "The customer's order number.",
                        },
                    },
                    "required": ["order_number"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "escalate_to_human",
                "description": "Create a handoff ticket for a human support agent.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Why the conversation needs human help.",
                        },
                        "urgency": {
                            "type": "string",
                            "enum": ["low", "normal", "high"],
                            "description": "How urgent the handoff is.",
                        },
                    },
                    "required": ["reason", "urgency"],
                },
            },
        },
    ]
    return tools


def call_rest_api(
    rest_api_endpoint: str,
    rest_api_key: str,
):
    params = {
        "orderid": 12345,
        "appid": rest_api_key,
    }
    try:
        response = requests.get(rest_api_endpoint, params=params)
        response.raise_for_status()

        data = response.json()

        return f"Order {params['orderid']} details: {data}"

    except requests.exceptions.RequestException as error:
        return f"ERROR: Rest API request failed: {error}"


def call_exchange_rate_api(
    exchange_rate_endpoint, exchange_rate_api_key, from_currency, to_currency
):
    url = f"{exchange_rate_endpoint}/{exchange_rate_api_key}/latest/{from_currency}"
    try:
        response = requests.get(url)

        response.raise_for_status()

        data = response.json()

        if data.get("result") != "success":
            return (
                f"ERROR: Exchange rate API error: "
                f"{data.get('error-type', 'Unknown error')}"
            )

        rate = data["conversion_rates"].get(to_currency.upper())

        if rate is None:
            return (
                f"ERROR: Currency '{to_currency}' not found. "
                "Available currencies vary by API."
            )
        return (
            f"Exchange rate: 1 {from_currency.upper()} = "
            f"{rate} {to_currency.upper()}"
        )
    except requests.exceptions.RequestException as error:
        return f"ERROR: Exchange rate API request failed: {error}"


def execute_tool(tool_name, tool_arguments):
    print(f"\n[TOOL EXECUTION] Calling '{tool_name}' with arguments: {tool_arguments}")
    if tool_name == "search_knowledge_base":
        question = tool_arguments.get("question")
        return search_knowledge_base(question)
    if tool_name == "check_refund_eligibility":
        order_number = tool_arguments.get("order_number")
        return check_refund_eligibility(order_number)
    if tool_name == "escalate_to_human":
        reason = tool_arguments.get("reason")
        urgency = tool_arguments.get("urgency", "normal")
        return escalate_to_human(reason, urgency)

    return f"ERROR: Unknown tool '{tool_name}'"


def search_knowledge_base(question):
    if not question:
        return "ERROR: Missing required argument: question"

    return (
        "Support policy: Refund requests require an order number. Standard returns "
        "are limited to 30 days, but documented product issue exceptions may still "
        "be eligible. Confirm the customer's email before starting a refund."
    )


def check_refund_eligibility(order_number):
    if not order_number:
        return "ERROR: Missing required argument: order_number"

    record = SAMPLE_REFUND_RECORDS.get(str(order_number))
    if record is None:
        return f"ERROR: No refund record found for order {order_number}."

    return json.dumps(
        {
            "order_number": str(order_number),
            "eligible": record["eligible"],
            "reason": record["reason"],
            "next_step": record["next_step"],
        }
    )


def escalate_to_human(reason, urgency):
    if not reason:
        return "ERROR: Missing required argument: reason"

    return json.dumps(
        {
            "ticket_id": "sample-ticket-001",
            "status": "created",
            "urgency": urgency,
            "reason": reason,
        }
    )


def execute_tool_with_retry(
    tool_name, tool_arguments, max_retries=3, backoff_seconds=1
):
    last_error = None

    for attempt in range(max_retries):
        result = execute_tool(tool_name, tool_arguments)
        if not result.startswith("ERROR:"):
            if attempt > 0:
                print(f"[TOOL EXECUTION] Retry {attempt} succeeded.")
            return result
        last_error = result
        wait_time = backoff_seconds * (2**attempt)
        if attempt < max_retries - 1:
            print(
                f"[TOOL EXECUTION] Attempt {attempt + 1} failed. "
                f"Retrying in {wait_time}s..."
            )
            time.sleep(wait_time)
    return f"ERROR: All {max_retries} attempts failed. Last error: {last_error}"
