import os
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FileSearchTool, MessageAttachment, FilePurpose
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(), conn_str=os.getenv('PROJECT_CONNECTION_STRING')
)

with project_client:
    # We will upload the local file and will use it for vector store creation.

    #upload a file
    file = project_client.agents.upload_file_and_poll(file_path='leave-pol.pdf', purpose=FilePurpose.AGENTS)
    print(f"Uploaded file, file ID: {file.id}")
    print(f'File details: {file}')

    # create a vector store with the file you uploaded
    vector_store = project_client.agents.create_vector_store_and_poll(file_ids=[file.id], name="my_vectorstore")
    print(f"Created vector store, vector store ID: {vector_store.id}")

    # create a file search tool
    file_search_tool = FileSearchTool(vector_store_ids=[vector_store.id])

    # notices that FileSearchTool as tool and tool_resources must be added or the agent will be unable to search the file
    agent = project_client.agents.create_agent(
        model="gpt-4o",
        name="my-agent",
        instructions="You are a helpful agent which provides answer ONLY from the search",
        tools=file_search_tool.definitions,
        tool_resources=file_search_tool.resources,
    )
    print(f"Created agent, agent ID: {agent.id}")
    print(f"agent details: {agent}")

    # Create a thread
    thread = project_client.agents.create_thread()
    print(f"Created thread, thread ID: {thread.id}")
    print(f"thread details: {thread}")

    # Create a message
    message = project_client.agents.create_message(
        thread_id=thread.id, role="user", content="What is excess annual leave?", attachments=[]
    )
    print(f"Created message, message ID: {message.id}")
    print(f"message details: {message}")

    run = project_client.agents.create_and_process_run(thread_id=thread.id, assistant_id=agent.id)
    print(f"Created run, run ID: {run.id}")
    print(f"run details: {run}")

    project_client.agents.delete_vector_store(vector_store.id)
    print("Deleted vector store")

    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")

    # Retrieve and Print Messages in a Clean Format
    messages = project_client.agents.list_messages(thread_id=thread.id)
    print(f"Messages: {messages}")

    messages_data = messages["data"]

    # Sort messages by creation time (ascending)
    sorted_messages = sorted(messages_data, key=lambda x: x["created_at"])
    print(len(sorted_messages))

    print("\n--- Thread Messages (sorted) ---")
    for msg in sorted_messages:
        print(f'msg:{msg}')
        role = msg["role"].upper()
        # Each 'content' is a list; get the first text block if present
        content_blocks = msg.get("content", [])
        text_value = ""
        if content_blocks and content_blocks[0]["type"] == "text":
            text_value = content_blocks[0]["text"]["value"]
        print(f"{role}: {text_value}")