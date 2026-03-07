import os
from dotenv import load_dotenv
from pathlib import Path
from azure.ai.agents.models import CodeInterpreterTool
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition

load_dotenv()

agent_name = "foundry-agent"
agent_description = "Foundry agent with a code-interpreter tool."

model_name = "gpt-4o"
model_instructions = "You politely help with math questions. Use the Code Interpreter tool when asked to visualize numbers."

question = "Draw a graph for a line with a slope of 4 and y-intercept of 9 and provide the file to me?"

project_client = AIProjectClient(
    endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

with project_client:

    openai_client = project_client.get_openai_client()

    code_interpreter = CodeInterpreterTool()

    # Create an agent version
    agent = project_client.agents.create_version(
        agent_name=agent_name,
        description=agent_description,
        definition=PromptAgentDefinition(
            model=model_name,
            instructions=model_instructions,
            tools=code_interpreter.definitions,
        ),
    )

    print(f"Created agent, ID: {agent.id}")

    # Create a conversation
    conversation = openai_client.conversations.create()
    print(f"Created conversation, ID: {conversation.id}")

    # Add a message to the conversation
    openai_client.conversations.items.create(
        conversation_id=conversation.id,
        items=[{"type": "message", "role": "user", "content": question}],
    )

    # Get response
    response = openai_client.responses.create(
        conversation=conversation.id,
        extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
        input="",
    )

    if response.status == "failed":
        print(f"\nResponse failed: {response.error}")

    # Fetch and log all messages
    messages = openai_client.conversations.items.list(conversation_id=conversation.id)

    for message in messages:
        if message.type != "message":
            continue

        for this_content in message.content:
            if this_content.type != "output_text":
                continue

            print(message)
            if this_content.annotations:
                for annotation in this_content.annotations:
                    # Save every image file in the message
                    container_id = annotation.container_id
                    file_id = annotation.file_id

                    file_name = f"{file_id}.png"
                    file_data = openai_client.containers.files.content.retrieve(
                        file_id, container_id=container_id
                    )

                    out_path = Path.cwd() / f"files/{file_name}"
                    with open(out_path, "wb") as f:
                        f.write(file_data.read())

                    print(f"\nSaved image file to: {out_path}")
