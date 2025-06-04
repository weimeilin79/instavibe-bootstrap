# adk_mcp_server.py
import asyncio
import json
import uvicorn
import os
from dotenv import load_dotenv

from mcp import types as mcp_types 
from mcp.server.lowlevel import Server

from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount, Route


from google.adk.tools.function_tool import FunctionTool


from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type

from instavibe import create_event,create_post
load_dotenv()
APP_HOST = os.environ.get("APP_HOST", "0.0.0.0")
APP_PORT = os.environ.get("APP_PORT",8080)


event_tool = FunctionTool(create_event)
post_tool = FunctionTool(create_post)

available_tools = {
    event_tool.name: event_tool,
    post_tool.name: post_tool,
}

# Create a named MCP Server instance
app = Server("adk-tool-mcp-server")
sse = SseServerTransport("/messages/")


@app.list_tools()
async def list_tools() -> list[mcp_types.Tool]:
  """MCP handler to list available tools."""
  # Convert the ADK tool's definition to MCP format
  mcp_tool_schema_event = adk_to_mcp_tool_type(event_tool)
  mcp_tool_schema_post = adk_to_mcp_tool_type(post_tool)
  print(f"MCP Server: Received list_tools request. \n MCP Server: Advertising tool: {mcp_tool_schema_event.name} and {mcp_tool_schema_post}")
  return [mcp_tool_schema_event,mcp_tool_schema_post]

@app.call_tool()
async def call_tool(
    name: str, arguments: dict
) -> list[mcp_types.TextContent | mcp_types.ImageContent | mcp_types.EmbeddedResource]:
  """MCP handler to execute a tool call."""
  print(f"MCP Server: Received call_tool request for '{name}' with args: {arguments}")

  # Look up the tool by name in our dictionary
  tool_to_call = available_tools.get(name)
  if tool_to_call:
    try:
      adk_response = await tool_to_call.run_async(
          args=arguments,
          tool_context=None,
      )
      print(f"MCP Server: ADK tool '{name}' executed successfully.")

      response_text = json.dumps(adk_response, indent=2)
      return [mcp_types.TextContent(type="text", text=response_text)]

    except Exception as e:
      print(f"MCP Server: Error executing ADK tool '{name}': {e}")
      # Creating a proper MCP error response might be more robust
      error_text = json.dumps({"error": f"Failed to execute tool '{name}': {str(e)}"})
      return [mcp_types.TextContent(type="text", text=error_text)]
  else:
      # Handle calls to unknown tools
      print(f"MCP Server: Tool '{name}' not found.")
      error_text = json.dumps({"error": f"Tool '{name}' not implemented."})
      return [mcp_types.TextContent(type="text", text=error_text)]

# --- MCP Remote Server ---
async def handle_sse(request):
  """Runs the MCP server over standard input/output."""
  # Use the stdio_server context manager from the MCP library
  async with sse.connect_sse(
    request.scope, request.receive, request._send
  ) as streams:
    await app.run(
        streams[0], streams[1], app.create_initialization_options()
    )

starlette_app = Starlette(
 debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=sse.handle_post_message),
    ],
)

if __name__ == "__main__":
  print("Launching MCP Server exposing ADK tools...")
  try:
    asyncio.run(uvicorn.run(starlette_app, host=APP_HOST, port=APP_PORT))
  except KeyboardInterrupt:
    print("\nMCP Server stopped by user.")
  except Exception as e:
    print(f"MCP Server encountered an error: {e}")
  finally:
    print("MCP Server process exiting.")
# --- End MCP Server ---