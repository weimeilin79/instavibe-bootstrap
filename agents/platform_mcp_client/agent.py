import asyncio
from contextlib import AsyncExitStack
from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams
import logging 
import os
import nest_asyncio # Import nest_asyncio


# Load environment variables from .env file in the parent directory
# Place this near the top, before using env vars like API keys
load_dotenv()
MCP_SERVER_URL=os.environ.get("MCP_SERVER_URL", "http://0.0.0.0:8080/sse")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
 
# --- Global variables ---
# Define them first, initialize as None
root_agent: LlmAgent | None = None
exit_stack: AsyncExitStack | None = None


async def get_tools_async():
  """Gets tools from the File System MCP Server."""
  print("Attempting to connect to MCP Filesystem server...")
  tools, exit_stack = await MCPToolset.from_server(
      connection_params=SseServerParams(url=MCP_SERVER_URL, headers={})
  )
  log.info("MCP Toolset created successfully.")

  return tools, exit_stack
 

async def get_agent_async():
  """
  Asynchronously creates the MCP Toolset and the LlmAgent.

  Returns:
      tuple: (LlmAgent instance, AsyncExitStack instance for cleanup)
  """
  tools, exit_stack = await get_tools_async()

  root_agent = LlmAgent(
      model='gemini-2.0-flash', # Adjust model name if needed based on availability
      name='social_agent',
      instruction="""
        You are a friendly and efficient assistant for the Instavibe social app.
        Your primary goal is to help users create posts and register for events using the available tools.

        When a user asks to create a post:
        1.  You MUST identify the **author's name** and the **post text**.
        2.  You MUST determine the **sentiment** of the post.
            - If the user explicitly states a sentiment (e.g., "make it positive", "this is a sad post", "keep it neutral"), use that sentiment. Valid sentiments are 'positive', 'negative', or 'neutral'.
            - **If the user does NOT provide a sentiment, you MUST analyze the post text yourself, infer the most appropriate sentiment ('positive', 'negative', or 'neutral'), and use this inferred sentiment directly for the tool call. Do NOT ask the user to confirm your inferred sentiment. Simply state the sentiment you've chosen as part of a summary if you confirm the overall action.**
        3.  Once you have the `author_name`, `text`, and `sentiment` (either provided or inferred), you will prepare to call the `create_post` tool with these three arguments.

        When a user asks to create an event or register for one:
        1.  You MUST identify the **event name**, the **event date**, and the **attendee's name**.
        2.  For the `event_date`, aim to get it in a structured format if possible (e.g., "YYYY-MM-DDTHH:MM:SSZ" or "tomorrow at 3 PM"). If the user provides a vague date, you can ask for clarification or make a reasonable interpretation. The tool expects a string.
        3.  Once you have the `event_name`, `event_date`, and `attendee_name`, you will prepare to call the `create_event` tool with these three arguments.

        General Guidelines:
        - If any required information for an action (like author_name for a post, or event_name for an event) is missing from the user's initial request, politely ask the user for the specific missing pieces of information.
        - Before executing an action (calling a tool), you can optionally provide a brief summary of what you are about to do (e.g., "Okay, I'll create a post for [author_name] saying '[text]' with a [sentiment] sentiment."). This summary should include the inferred sentiment if applicable, but it should not be phrased as a question seeking validation for the sentiment.
        - Use only the provided tools. Do not try to perform actions outside of their scope.

      """,
        tools=tools,
  )
  print("LlmAgent created.")

  # Return both the agent and the exit_stack needed for cleanup
  return root_agent, exit_stack


async def initialize():
   """Initializes the global root_agent and exit_stack."""
   global root_agent, exit_stack
   if root_agent is None:
       log.info("Initializing agent...")
       root_agent, exit_stack = await get_agent_async()
       if root_agent:
           log.info("Agent initialized successfully.")
       else:
           log.error("Agent initialization failed.")
       
   else:
       log.info("Agent already initialized.")

def _cleanup_sync():
    """Synchronous wrapper to attempt async cleanup."""
    if exit_stack:
        log.info("Attempting to close MCP connection via atexit...")
        try:
            asyncio.run(exit_stack.aclose())
            log.info("MCP connection closed via atexit.")
        except Exception as e:
            log.error(f"Error during atexit cleanup: {e}", exc_info=True)


nest_asyncio.apply()

log.info("Running agent initialization at module level using asyncio.run()...")
try:
    asyncio.run(initialize())
    log.info("Module level asyncio.run(initialize()) completed.")
except RuntimeError as e:
    log.error(f"RuntimeError during module level initialization (likely nested loops): {e}", exc_info=True)
except Exception as e:
    log.error(f"Unexpected error during module level initialization: {e}", exc_info=True)

