import asyncio
import json
import uvicorn
import os
from dotenv import load_dotenv

from mcp import types as mcp_types
from mcp.server.lowlevel import Server as MCPLowLevelServer # Alias to avoid confusion
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount

from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type

# Import our custom BigQuery tools
from .tools import custom_bq_tools

# Placeholder for MCP Toolbox for Databases
# from mcp_toolbox_database import get_database_tools # Speculative import

load_dotenv()
APP_HOST = os.environ.get("BQ_MCP_SERVER_HOST", "0.0.0.0")
APP_PORT = int(os.environ.get("BQ_MCP_SERVER_PORT", 8081)) # Different port from other services

all_mcp_exposed_tools = {}

# Add custom tools
for tool in custom_bq_tools:
    all_mcp_exposed_tools[tool.name] = tool
print(f"Loaded custom BQ tools: {list(all_mcp_exposed_tools.keys())}")

# Placeholder: Add tools from MCP Toolbox for Databases
# db_tools = []
# try:
#     db_tools = get_database_tools() # Speculative
#     for tool in db_tools:
#         if tool.name not in all_mcp_exposed_tools: # Avoid overwriting
#             all_mcp_exposed_tools[tool.name] = tool
#         else:
#             print(f"Warning: Tool '{tool.name}' from DB toolbox already exists from custom tools. Custom tool takes precedence.")
#     print(f"Loaded database tools: {[tool.name for tool in db_tools]}")
# except ImportError:
#     print("MCP Toolbox for Databases not found or 'get_database_tools' not available. Skipping.")
# except Exception as e:
#     print(f"Error loading MCP Toolbox for Databases: {e}")

print(f"All MCP exposed tools: {list(all_mcp_exposed_tools.keys())}")

# Create a named MCP Server instance
app_mcp = MCPLowLevelServer(name="bq-advisor-mcp-server") # Use the alias
sse_transport = SseServerTransport("/messages/") # Define the transport

@app_mcp.list_tools()
async def list_tools_handler() -> list[mcp_types.Tool]:
    print(f"BQ Advisor MCP Server: Received list_tools request.")
    mcp_tool_schemas = []
    for tool_name, adk_tool_instance in all_mcp_exposed_tools.items():
        try:
            mcp_schema = adk_to_mcp_tool_type(adk_tool_instance)
            mcp_tool_schemas.append(mcp_schema)
        except Exception as e:
            print(f"Error converting ADK tool '{tool_name}' to MCP type: {e}")
    print(f"BQ Advisor MCP Server: Advertising tools: {[t.name for t in mcp_tool_schemas]}")
    return mcp_tool_schemas

@app_mcp.call_tool()
async def call_tool_handler(
    name: str, arguments: dict
) -> list[mcp_types.TextContent | mcp_types.ImageContent | mcp_types.EmbeddedResource]:
    print(f"BQ Advisor MCP Server: Received call_tool request for '{name}' with args: {arguments}")
    tool_to_call = all_mcp_exposed_tools.get(name)
    if tool_to_call:
        try:
            # ADK FunctionTool's run_async expects 'args' as a dict
            adk_response_json_str = await tool_to_call.run_async(args=arguments, tool_context=None)
            # Assuming the tool returns a JSON string, as per our custom tool implementation
            # No need to json.dumps again if already a string. If it's a dict, then dumps.
            # Our tools return JSON strings.
            print(f"BQ Advisor MCP Server: ADK tool '{name}' executed. Response: {adk_response_json_str[:100]}...")
            return [mcp_types.TextContent(type="text", text=adk_response_json_str)]
        except Exception as e:
            print(f"BQ Advisor MCP Server: Error executing ADK tool '{name}': {e}", exc_info=True)
            error_text = json.dumps({"error": f"Failed to execute tool '{name}': {str(e)}"})
            return [mcp_types.TextContent(type="text", text=error_text)]
    else:
        print(f"BQ Advisor MCP Server: Tool '{name}' not found.")
        error_text = json.dumps({"error": f"Tool '{name}' not implemented."})
        return [mcp_types.TextContent(type="text", text=error_text)]

# --- Starlette App to host MCP Server ---
async def handle_sse_request(request):
    async with sse_transport.connect_sse(request.scope, request.receive, request._send) as streams:
        await app_mcp.run(streams[0], streams[1], app_mcp.create_initialization_options())

starlette_app = Starlette(
    debug=True, # Set to False in production
    routes=[
        Route("/sse", endpoint=handle_sse_request, methods=["GET", "POST"]), # Allow POST for some clients
        Mount("/messages/", app=sse_transport.handle_post_message),
    ],
)

if __name__ == "__main__":
    print(f"Launching BQ Advisor MCP Server on {APP_HOST}:{APP_PORT}...")
    try:
        # Ensure nest_asyncio is applied if not already, as uvicorn.run can be tricky with existing loops
        import nest_asyncio
        nest_asyncio.apply()
        uvicorn.run(starlette_app, host=APP_HOST, port=APP_PORT, log_level="info")
    except KeyboardInterrupt:
        print("BQ Advisor MCP Server stopped by user.")
    except Exception as e:
        print(f"BQ Advisor MCP Server encountered an error: {e}", exc_info=True)
    finally:
        print("BQ Advisor MCP Server process exiting.")
