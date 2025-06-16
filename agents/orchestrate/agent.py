import asyncio
import json
import os
import uuid
import nest_asyncio 

from typing import Any, AsyncIterator

import httpx

from a2a.client import A2ACardResolver
from a2a.types import (
    AgentCard,
    MessageSendParams,
    Part,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task,
    TaskState,
)
try:
    from remote_agent_connection import ( 
        RemoteAgentConnections,
        TaskUpdateCallback,
    )
except ImportError:
    from orchestrate.remote_agent_connection import ( 
        RemoteAgentConnections,
        TaskUpdateCallback,
    )
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.tool_context import ToolContext
import logging 
log = logging.getLogger(__name__)
 

load_dotenv()

root_agent: LlmAgent | None = None

REMOTE_AGENT_ADDRESSES_STR = os.getenv("REMOTE_AGENT_ADDRESSES", "")
REMOTE_AGENT_ADDRESSES = [addr.strip() for addr in REMOTE_AGENT_ADDRESSES_STR.split(',') if addr.strip()]

log.info(f"Remote Agent Addresses: {REMOTE_AGENT_ADDRESSES}")

def convert_part(part: Part, tool_context: ToolContext):
    """Convert a part to text. Only text parts are supported."""
    if part.type == 'text':
        return part.text

    return f'Unknown type: {part.type}'


def convert_parts(parts: list[Part], tool_context: ToolContext):
    """Convert parts to text."""
    rval = []
    for p in parts:
        rval.append(convert_part(p, tool_context))
    return rval


def create_send_message_payload(
    text: str, task_id: str | None = None, context_id: str | None = None
) -> dict[str, Any]:
    """Helper function to create the payload for sending a task."""
    payload: dict[str, Any] = {
        'message': {
            'role': 'user',
            'parts': [{'type': 'text', 'text': text}],
            'messageId': uuid.uuid4().hex,
        },
    }

    if task_id:
        payload['message']['taskId'] = task_id

    if context_id:
        payload['message']['contextId'] = context_id
    return payload


class HostAgent:
  """The orchestrate agent.

  This is the agent responsible for choosing which remote agents to send
  tasks to and coordinate their work.
  """

  def __init__(
        self,
        task_callback: TaskUpdateCallback | None = None,
    ):
        self.task_callback = task_callback
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        self.agents: str = ''

  #REPLACE ME REG AGENT CARD

  #REPLACE ME CREATE AGENT

  #REPLACE ME INSTRUCTIONS

  
  def check_active_agent(self, context: ReadonlyContext):
        state = context.state
        if (
            'session_id' in state
            and 'session_active' in state
            and state['session_active']
            and 'active_agent' in state
        ):
            return {'active_agent': f'{state["active_agent"]}'}
        return {'active_agent': 'None'}

  def before_model_callback(
        self, callback_context: CallbackContext, llm_request
    ):
        state = callback_context.state
        if 'session_active' not in state or not state['session_active']:
            if 'session_id' not in state:
                state['session_id'] = str(uuid.uuid4())
            state['session_active'] = True

  def list_remote_agents(self):
        """List the available remote agents you can use to delegate the task."""
        if not self.cards:
            return []

        remote_agent_info = []
        for card in self.cards.values():
            print(f'Found agent card: {card.model_dump(exclude_none=True)}')
            print('=' * 100)
            remote_agent_info.append(
                {'name': card.name, 'description': card.description}
            )
        return remote_agent_info

  async def send_message(
        self, agent_name: str, task: str, tool_context: ToolContext
    ):
        """Sends a task to remote seller agent.

        This will send a message to the remote agent named agent_name.

        Args:
            agent_name: The name of the agent to send the task to.
            task: The comprehensive conversation context summary
                and goal to be achieved regarding user inquiry and purchase request.
            tool_context: The tool context this method runs in.

        Yields:
            A dictionary of JSON data.
        """
        if agent_name not in self.remote_agent_connections:
            raise ValueError(f'Agent {agent_name} not found')
        state = tool_context.state
        state['active_agent'] = agent_name
        client = self.remote_agent_connections[agent_name]

        if not client:
            raise ValueError(f'Client not available for {agent_name}')
        task_id = state['task_id'] if 'task_id' in state else str(uuid.uuid4())

        if 'context_id' in state:
            context_id = state['context_id']
        else:
            context_id = str(uuid.uuid4())

        message_id = ''
        metadata = {}
        if 'input_message_metadata' in state:
            metadata.update(**state['input_message_metadata'])
            if 'message_id' in state['input_message_metadata']:
                message_id = state['input_message_metadata']['message_id']
        if not message_id:
            message_id = str(uuid.uuid4())

        payload = {
            'message': {
                'role': 'user',
                'parts': [
                    {'type': 'text', 'text': task}
                ],  # Use the 'task' argument here
                'messageId': message_id,
            },
        }

        if task_id:
            payload['message']['taskId'] = task_id

        if context_id:
            payload['message']['contextId'] = context_id

        message_request = SendMessageRequest(
            id=message_id, params=MessageSendParams.model_validate(payload)
        )
        send_response: SendMessageResponse = await client.send_message(
            message_request=message_request
        )
        print('send_response', send_response.model_dump_json(exclude_none=True, indent=2))

        if not isinstance(send_response.root, SendMessageSuccessResponse):
            print('received non-success response. Aborting get task ')
            return

        if not isinstance(send_response.root.result, Task):
            print('received non-task response. Aborting get task ')
            return

        return send_response.root.result




async def initialize():
   """Initializes the global root_agent and exit_stack."""
   global root_agent
   if root_agent is None:
       log.info("Initializing agent...")
       host_agent_instance = await HostAgent.create(REMOTE_AGENT_ADDRESSES)
       root_agent = host_agent_instance.create_agent()
       if root_agent:
           log.info("Agent initialized successfully.")
       else:
           log.error("Agent initialization failed.")
       
   else:
       log.info("Agent already initialized.")

def _cleanup_sync():
    """Synchronous wrapper to attempt async cleanup."""
    log.info("MCP connection cleanup is now handled externally.")
    # No specific cleanup action needed here as exit_stack is managed elsewhere.
    pass 


nest_asyncio.apply()

log.info("Running agent initialization at module level using asyncio.run()...")
try:
    asyncio.run(initialize())
    log.info("Module level asyncio.run(initialize()) completed.")
except RuntimeError as e:
    log.error(f"RuntimeError during module level initialization (likely nested loops): {e}", exc_info=True)
except Exception as e:
    log.error(f"Unexpected error during module level initialization: {e}", exc_info=True)
