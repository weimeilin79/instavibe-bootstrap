import asyncio
import json
import os
import uuid
from typing import Any

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

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# --- Configuration ---
REMOTE_AGENT_ADDRESSES_STR = os.getenv("REMOTE_AGENT_ADDRESSES", "")
REMOTE_AGENT_ADDRESSES = [addr.strip() for addr in REMOTE_AGENT_ADDRESSES_STR.split(',') if addr.strip()]

log.info(f"Remote Agent Addresses: {REMOTE_AGENT_ADDRESSES}")

# --- Helper Functions ---
def create_send_message_payload(
    text: str, task_id: str | None = None, context_id: str | None = None
) -> dict[str, Any]:
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


# --- Main Agent Class ---
class HostAgent:
    """The orchestrate agent with a special diagnostic initializer."""

    def __init__(self, task_callback: TaskUpdateCallback | None = None):
        log.info("HostAgent instance created in memory (uninitialized).")
        self.task_callback = task_callback
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        self.agents: str = ''
        self.is_initialized = False

    async def _initialize(self):
        """
        DIAGNOSTIC VERSION: This method will test each connection one-by-one
        with aggressive logging to force the hidden error to appear.
        """
        if not REMOTE_AGENT_ADDRESSES or not REMOTE_AGENT_ADDRESSES[0]:
            log.error("CRITICAL FAILURE: REMOTE_AGENT_ADDRESSES environment variable is empty. Cannot proceed.")
            self.is_initialized = True
            return

        #REPLACE ME REG AGENT CARD

        log.error("STEP 6: Finished attempting all connections.")
        if not self.remote_agent_connections:
            log.error("FINAL VERDICT: The loop finished, but the remote agent list is still empty.")
        else:
            agent_info = [json.dumps({'name': c.name, 'description': c.description}) for c in self.cards.values()]
            self.agents = '\n'.join(agent_info)
            log.info(f"--- FINAL SUCCESS: Initialization complete. {len(self.remote_agent_connections)} agents loaded. ---")
        
        self.is_initialized = True

    async def before_agent_callback(self, callback_context: CallbackContext):
        log.info("`before_agent_callback` triggered.")
        if not self.is_initialized:
            await self._initialize()
        
        state = callback_context.state
        if 'session_active' not in state or not state['session_active']:
            if 'session_id' not in state:
                state['session_id'] = str(uuid.uuid4())
            state['session_active'] = True

    #REPLACE ME INSTRUCTIONS

    async def send_message(self, agent_name: str, task: str, tool_context: ToolContext):
        if agent_name not in self.remote_agent_connections:
            log.error(f"LLM tried to call '{agent_name}' but it was not found. Available agents: {list(self.remote_agent_connections.keys())}")
            raise ValueError(f"Agent '{agent_name}' not found.")
        
        state = tool_context.state
        state['active_agent'] = agent_name
        client = self.remote_agent_connections[agent_name]

        task_id = state.get('task_id', str(uuid.uuid4()))
        context_id = state.get('context_id', str(uuid.uuid4()))
        message_id = state.get('input_message_metadata', {}).get('message_id', str(uuid.uuid4()))

        payload = create_send_message_payload(task, task_id, context_id)
        payload['message']['messageId'] = message_id

        message_request = SendMessageRequest(id=message_id, params=MessageSendParams.model_validate(payload))
        
        send_response: SendMessageResponse = await client.send_message(message_request=message_request)
        
        if not isinstance(send_response.root, SendMessageSuccessResponse) or not isinstance(send_response.root.result, Task):
            return None
        return send_response.root.result

    def check_active_agent(self, context: ReadonlyContext):
        state = context.state
        if 'session_active' in state and state['session_active'] and 'active_agent' in state:
            return {'active_agent': f'{state["active_agent"]}'}
        return {'active_agent': 'None'}

    def list_remote_agents(self):
        if not self.cards:
            return []
        remote_agent_info = []
        for card in self.cards.values():
            remote_agent_info.append({'name': card.name, 'description': card.description})
        return remote_agent_info

    #REPLACE ME CREATE AGENT

# --- Top-Level Execution ---

log.info("Module-level code is running. Creating uninitialized agent object...")
host_agent_singleton = HostAgent()
root_agent = host_agent_singleton.create_agent()
log.info("Module-level setup finished. 'root_agent' is populated.")