# Attempt to import the initialized agent object 'root_agent'
# from agents.platform_mcp_client.agent after ensuring its initialization.
from agents.platform_mcp_client import agent as platform_mcp_agent # Alias to avoid confusion
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import ReasoningEngine
import asyncio

# Ensure the agent is initialized before trying to use it.
# The agents.platform_mcp_client.agent module calls asyncio.run(initialize()) at the module level.
# This should mean platform_mcp_agent.root_agent is populated upon import.
# The agent.py also uses nest_asyncio.apply() which allows subsequent asyncio.run() calls,
# like the one used here to retrieve the agent.

async def get_initialized_agent():
    # This check and call to initialize() is a fallback.
    # Ideally, root_agent is already initialized.
    if platform_mcp_agent.root_agent is None:
        print("platform_mcp_agent.root_agent is None, attempting to call initialize()...")
        await platform_mcp_agent.initialize()
    return platform_mcp_agent.root_agent

# Get the agent object
# We need to run the async function to get the agent.
# asyncio.run() is used here. This is possible even if agent.py already started an event loop
# because agent.py calls nest_asyncio.apply().
try:
    agent_obj = asyncio.run(get_initialized_agent())
    if agent_obj is None:
        raise ValueError("Failed to initialize or retrieve the platform_mcp_client agent (platform_mcp_agent.root_agent is None even after get_initialized_agent).")
except Exception as e:
    print(f"Error initializing or retrieving platform_mcp_client agent: {e}")
    raise

display_name = "Platform MCP Client Agent"
description = "This agent interacts with the MCP toolset and other platform services."

print(f"Attempting to deploy {display_name}...")

# Deploy the agent to Vertex AI Agent Engine
remote_agent = ReasoningEngine.create(
    agent_obj,  # The initialized agent object
    requirements=[
        "google-cloud-aiplatform[adk,agent_engines]==1.91.0",
        "Flask==3.1.0",
        "mcp[cli]==1.7.1",
        "google-adk==0.4.0",
        "python-dateutil==2.9.0.post0",
        "humanize==4.12.3",
        "nest_asyncio==1.6.0", # Crucial for nested asyncio.run() calls
        "asyncclick==8.1.8.0",
        "a2a_common-0.1.0-py3-none-any.whl",
        "deprecated==1.2.18",
    ],
    display_name=display_name,
    description=description,
)

print(f"{display_name} deployed successfully: {remote_agent.name}")
print(f"View in console: {remote_agent.resource_name}")
