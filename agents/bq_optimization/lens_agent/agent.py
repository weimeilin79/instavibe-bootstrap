import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams
import logging
import nest_asyncio # Import nest_asyncio
import atexit

# Apply nest_asyncio to allow running asyncio.run() at module level if an event loop is already running
# This is useful in some environments like Jupyter or when other async libs are used.
nest_asyncio.apply()

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

BQ_MCP_SERVER_URL = os.getenv("BQ_MCP_SERVER_URL")

# Global variables for MCP tools and exit stack for cleanup
mcp_tools_global = [] # Initialize as empty list
mcp_exit_stack_global = None

async def _initialize_mcp_tools_async():
    global mcp_tools_global, mcp_exit_stack_global
    if BQ_MCP_SERVER_URL:
        log.info(f"Attempting to connect to BigQuery MCP Server at: {BQ_MCP_SERVER_URL}")
        try:
            tools, exit_stack = await MCPToolset.from_server(
                connection_params=SseServerParams(url=BQ_MCP_SERVER_URL, headers={})
            )
            mcp_tools_global = tools
            mcp_exit_stack_global = exit_stack
            log.info(f"Successfully connected to BigQuery MCP Server and retrieved tools: {[tool.name for tool in mcp_tools_global]}")
        except Exception as e:
            log.error(f"Failed to connect to BigQuery MCP Server or retrieve tools: {e}", exc_info=True)
            mcp_tools_global = [] # Ensure it's an empty list on failure
    else:
        log.warning("BQ_MCP_SERVER_URL is not set. BigQueryLensAgent will operate without MCP tools.")
        mcp_tools_global = []

# Run the async initialization at module load time
log.info("Running BigQueryLensAgent MCP tool initialization at module level...")
try:
    # Check if an event loop is already running. If so, nest_asyncio should handle it.
    # If not, asyncio.run will create one.
    asyncio.run(_initialize_mcp_tools_async())
    log.info("BigQueryLensAgent MCP tool initialization completed.")
except RuntimeError as e:
    if "cannot run current event loop" in str(e).lower() or "Nesting asyncio event loops is not supported" in str(e):
        log.warning(f"Asyncio loop issue during module-level init (nest_asyncio should prevent this): {e}. Tools might not be loaded.")
    else:
        log.error(f"RuntimeError during module-level MCP init: {e}", exc_info=True)
except Exception as e:
    log.error(f"Unexpected error during module-level MCP init: {e}", exc_info=True)


bigquery_lens_agent = LlmAgent(
    name="BigQueryLensAgent",
    model="gemini-2.0-flash",
    description="Analyzes BigQuery queries and provides optimization recommendations using specialized tools.",
    instruction="""
    You are a specialized AI assistant for BigQuery optimization. You receive queries or questions
    about BigQuery from another agent. Your task is to use the available BigQuery analysis tools
    to provide detailed and actionable optimization recommendations.

    When you receive a request:
    1. Understand the user's underlying question or the query they want to optimize.
    2. Identify the appropriate BigQuery analysis tool(s) to use from your toolset.
       (Example tools you might have: 'analyze_query_cost', 'get_schema_recommendations', 'check_slot_usage')
    3. Call the selected tool(s) with the necessary parameters based on the user's request.
    4. Based on the output from the tool(s), formulate a clear, concise, and actionable recommendation.
    5. If no specific tools apply or if tools return no specific advice, or if tools are unavailable,
       state that you've analyzed the query and provide general BigQuery best practices relevant to the query, if possible.
       If tools are unavailable due to configuration or connection issues, mention this fact.
    6. Return this recommendation as your response.

    If BQ_MCP_SERVER_URL was not set or tool loading failed, explain that you cannot access specialized tools
    and can only provide general advice, mentioning the tool access issue.
    """,
    tools=mcp_tools_global, # Use the globally initialized tools
)

def _cleanup_mcp_sync():
    global mcp_exit_stack_global
    if mcp_exit_stack_global:
        log.info("Attempting to close MCP connection for BigQueryLensAgent via atexit...")
        try:
            asyncio.run(mcp_exit_stack_global.aclose())
            log.info("MCP connection for BigQueryLensAgent closed via atexit.")
        except Exception as e:
            log.error(f"Error during BigQueryLensAgent MCP atexit cleanup: {e}", exc_info=True)

atexit.register(_cleanup_mcp_sync)

# The root_agent is what the ADK framework will typically look for.
# It's now initialized with tools loaded at module level.
root_agent = bigquery_lens_agent
