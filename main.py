import sys

from clients import create_content_safety_client, create_openai_client
from config import load_config
from display import (
    format_reply,
    print_performance_metrics,
    print_routing_explanation,
)
from prompts import build_system_instruction, count_tokens, truncate_system_instruction
from routing import route_to_model
from safety import is_text_safe


def main() -> None:
    config = load_config()
    openai_client = create_openai_client(config)
    content_safety_client = create_content_safety_client(config)

    system_instruction = build_system_instruction(
        user_name=config.user_name,
        user_role=config.user_role,
        session_state=config.session_state,
        grounding_results=config.grounding_results,
    )

    token_count = count_tokens(system_instruction, model=config.llm_deployment_name)
    if token_count > config.max_system_tokens:
        system_instruction, token_count = truncate_system_instruction(
            system_instruction,
            model=config.llm_deployment_name,
            max_tokens=config.max_system_tokens,
        )

    system_message = {"role": "system", "content": system_instruction}

    # user_message_text = (
    #     "My order number is 12345. I want to return my 70 inch TV. Can you help me?"
    # )
    
    user_message_text = (
        "This is a simple request: I need to understand what is happening to my "
        "refund request. Can you analyze the situation and tell me why it is "
        "taking so long?"
    )
    # user_message_text = "Hello, how are you?"

    if not is_text_safe(
        content_safety_client,
        user_message_text,
        config.severity_threshold,
    ):
        format_reply(config.safe_response)
        return

    user_message = {"role": "user", "content": user_message_text}
    messages = [system_message, user_message]

    result = route_to_model(
        openai_client,
        user_message_text,
        messages,
        llm_deployment_name=config.llm_deployment_name,
        slm_deployment_name=config.slm_deployment_name,
        use_slm_classifier=True,
    )

    if result.reply is None:
        print("ERROR: Failed to get response from model.")
        sys.exit(1)

    if not is_text_safe(
        content_safety_client,
        result.reply,
        config.severity_threshold,
    ):
        format_reply(config.safe_response)
    else:
        format_reply(result.reply)

    print_performance_metrics(result)
    print_routing_explanation(result)


if __name__ == "__main__":
    main()
