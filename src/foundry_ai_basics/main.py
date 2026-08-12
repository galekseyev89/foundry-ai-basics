import sys
from uuid import uuid4

from foundry_ai_basics.ai.prompts import (
    build_system_instruction,
    count_tokens,
    truncate_system_instruction,
)
from foundry_ai_basics.ai.routing import route_to_model
from foundry_ai_basics.ai.safety import is_text_safe
from foundry_ai_basics.clients import (
    create_content_safety_client,
    create_mcp_client,
    create_openai_client,
    create_search_client,
    create_search_index_client,
)
from foundry_ai_basics.ai.search import (
    create_index,
    upload_documents,
    search_documents,
)

from foundry_ai_basics.config import load_config
from foundry_ai_basics.display import (
    format_reply,
    print_performance_metrics,
    read_user_message,
)
from foundry_ai_basics.open_telemetry import OpenTelemetry


def main() -> None:
    config = load_config()

    openai_client = create_openai_client(config)

    content_safety_client = create_content_safety_client(config)

    search_index_client = create_search_index_client(config)
    search_client = create_search_client(config)

    mcp_client = create_mcp_client(config)
    open_telemetry_client = OpenTelemetry(
        config.application_insights_connection_string,
        user_name=config.user_name,
        user_role=config.user_role,
    )
    open_telemetry_client.set_conversation_id(str(uuid4()))

    # Step 1: Create index
    create_index(search_index_client, config.search_index_name)

    # Step 2: Upload documents
    upload_documents(
        search_client,
        openai_client,
        config.embedding_model_deployment_name,
    )

    messages: list[dict[str, str]] = []

    while True:
        user_message_text = read_user_message()
        if not user_message_text:
            print("No message entered. Exiting.")
            break

        if not is_text_safe(
            content_safety_client,
            user_message_text,
            config.severity_threshold,
        ):
            format_reply(config.safe_response)
            continue

        grounding_results = search_documents(
            search_client,
            openai_client,
            config.embedding_model_deployment_name,
            user_message_text,
        )

        system_instruction = build_system_instruction(
            user_name=config.user_name,
            user_role=config.user_role,
            session_state=config.session_state,
            grounding_results=grounding_results,
        )

        token_count = count_tokens(system_instruction, model=config.llm_deployment_name)
        if token_count > config.max_system_tokens:
            system_instruction, token_count = truncate_system_instruction(
                system_instruction,
                model=config.llm_deployment_name,
                max_tokens=config.max_system_tokens,
            )

        system_message = {"role": "system", "content": system_instruction}
        if messages:
            messages[0] = system_message
        else:
            messages.append(system_message)

        user_message = {"role": "user", "content": user_message_text}
        messages.append(user_message)

        result = route_to_model(
            openai_client,
            user_message_text,
            config.routing,
            messages=messages,
            mcp_client=mcp_client,
            open_telemetry_client=open_telemetry_client,
        )

        if result.reply is None:
            print("ERROR: Failed to get response from model.")
            sys.exit(1)

        if not is_text_safe(
            content_safety_client,
            result.reply,
            config.severity_threshold,
        ):
            reply_text = config.safe_response
        else:
            reply_text = result.reply

        format_reply(reply_text)
        messages.append({"role": "assistant", "content": reply_text})

        print_performance_metrics(result)

    open_telemetry_client.flush()


if __name__ == "__main__":
    main()
