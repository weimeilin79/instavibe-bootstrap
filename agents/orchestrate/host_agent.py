import sys
import asyncio
import functools
import json
import uuid
import threading
from typing import List, Optional, Callable


from google.genai import types
import base64

from google.adk import Agent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext
from remote.remote_agent_connection import (
    RemoteAgentConnections,
    TaskUpdateCallback
)
from common.client import A2ACardResolver
from common.types import (
    AgentCard,
    Message,
    TaskState,
    Task,
    TaskSendParams,
    TextPart,
    DataPart,
    Part,
    TaskStatusUpdateEvent,
)


class HostAgent:
  """The orchestrate agent.

  This is the agent responsible for choosing which remote agents to send
  tasks to and coordinate their work.
  """

  def __init__(
      self,
      remote_agent_addresses: List[str],
      task_callback: TaskUpdateCallback | None = None
  ):
    self.task_callback = task_callback
    self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
    self.cards: dict[str, AgentCard] = {}
    for address in remote_agent_addresses:
      card_resolver = A2ACardResolver(address)
      card = card_resolver.get_agent_card()
      remote_connection = RemoteAgentConnections(card)
      self.remote_agent_connections[card.name] = remote_connection
      self.cards[card.name] = card
    agent_info = []
    for ra in self.list_remote_agents():
      agent_info.append(json.dumps(ra))
    self.agents = '\n'.join(agent_info)

  def register_agent_card(self, card: AgentCard):
    remote_connection = RemoteAgentConnections(card)
    self.remote_agent_connections[card.name] = remote_connection
    self.cards[card.name] = card
    agent_info = []
    for ra in self.list_remote_agents():
      agent_info.append(json.dumps(ra))
    self.agents = '\n'.join(agent_info)

  def create_agent(self) -> Agent:
    return Agent(
        model="gemini-2.0-flash",
        name="orchestrate_agent",
        instruction=self.root_instruction,
        before_model_callback=self.before_model_callback,
        description=(
            "This agent orchestrates the decomposition of the user request into"
            " tasks that can be performed by the child agents."
        ),
        tools=[
            self.list_remote_agents,
            self.send_task,
        ],
    )

  def root_instruction(self, context: ReadonlyContext) -> str:
    current_agent = self.check_state(context)
    return f"""

    You are an expert AI Orchestrator. Your primary responsibility is to intelligently interpret user requests, plan the necessary sequence of actions if multiple steps are involved, and delegate them to the most appropriate specialized remote agents. You do not perform the tasks yourself but manage their assignment, sequence, and can monitor their status.

    Core Workflow & Decision Making:

    1.  **Understand User Intent & Complexity:**
        *   Carefully analyze the user's request to determine the core task(s) they want to achieve. Pay close attention to keywords and the overall goal.
        *   **Identify if the request requires a single agent or a sequence of actions from multiple agents.** For example, "Analyze John Doe's profile and then create a positive post about his recent event attendance" would require two agents in sequence.

    2.  **Agent Discovery & Selection:**
        *   Use `list_remote_agents` to get an up-to-date list of available remote agents and understand their specific capabilities (e.g., what kind of requests each agent is designed to handle and what data they output).
        *   Based on the user's intent:
            *   For **single-step requests**, select the single most appropriate agent.
            *   For **multi-step requests**, identify all necessary agents and determine the logical order of their execution.

    3.  **Task Planning & Sequencing (for Multi-Step Requests):**
        *   Before delegating, outline the sequence of agent tasks.
        *   Identify dependencies: Does Agent B need information from Agent A's completed task?
        *   Plan to execute tasks sequentially if there are dependencies, waiting for the completion of a prerequisite task before initiating the next one.

    4.  **Task Delegation & Management:**
        *   **For New Single Requests or the First Step in a Sequence:** Use `create_task`. Your `create_task` call MUST include:
            *   The `remote_agent_name` you've selected.
            *   The `user_request` or all necessary parameters extracted from the user's input, formatted in a way the target agent will understand.
        *   **For Subsequent Steps in a Sequence:**
            *   Wait for the preceding task to complete (you may need to use `check_pending_task_states` to confirm completion).
            *   Once the prerequisite task is done, gather any necessary output from it.
            *   Then, use `create_task` for the next agent in the sequence, providing it with the user's original relevant intent and any necessary data obtained from the previous agent's task.
        *   **For Ongoing Interactions with an Active Agent (within a single step):** If the user is providing follow-up information related to a task *currently assigned* to a specific agent, use the `update_task` tool.
        *   **Monitoring:** Use `check_pending_task_states` to check the status of any delegated tasks, especially when managing sequences or if the user asks for an update.

    **Communication with User:**

    *   When you delegate a task (or the first task in a sequence), clearly inform the user which remote agent is handling it.
    *   For multi-step requests, you can optionally inform the user of the planned sequence (e.g., "Okay, first I'll ask the 'Social Profile Agent' to analyze the profile, and then I'll have the 'Instavibe Posting Agent' create the post.").
    *   If waiting for a task in a sequence to complete, you can inform the user (e.g., "The 'Social Profile Agent' is currently processing. I'll proceed with the post once that's done.").
    *   If the user's request is ambiguous, if necessary information is missing for any agent in the sequence, or if you are unsure about the plan, proactively ask the user for clarification.
    *   Rely strictly on your tools and the information they provide.

    **Important Reminders:**
    *   Always prioritize selecting the correct agent(s) based on their documented purpose.
    *   Ensure all information required by the chosen remote agent is included in the `create_task` or `update_task` call, including outputs from previous agents if it's a sequential task.
    *   Focus on the most recent parts of the conversation for immediate context, but maintain awareness of the overall goal, especially for multi-step requests.

    Agents:
    {self.agents}

    Current agent: {current_agent['active_agent']}
    """

  
  def check_state(self, context: ReadonlyContext):
    state = context.state
    if ('session_id' in state and
        'session_active' in state and
        state['session_active'] and
        'agent' in state):
      return {"active_agent": f'{state["agent"]}'}
    return {"active_agent": "None"}

  def before_model_callback(self, callback_context: CallbackContext, llm_request):
    state = callback_context.state
    if 'session_active' not in state or not state['session_active']:
      if 'session_id' not in state:
        state['session_id'] = str(uuid.uuid4())
      state['session_active'] = True

  def list_remote_agents(self):
    """List the available remote agents you can use to delegate the task."""
    if not self.remote_agent_connections:
      return []

    remote_agent_info = []
    for card in self.cards.values():
      remote_agent_info.append(
          {"name": card.name, "description": card.description}
      )
    return remote_agent_info

  async def send_task(
      self,
      agent_name: str,
      message: str,
      tool_context: ToolContext):
    """Sends a task either streaming (if supported) or non-streaming.

    This will send a message to the remote agent named agent_name.

    Args:
      agent_name: The name of the agent to send the task to.
      message: The message to send to the agent for the task.
      tool_context: The tool context this method runs in.

    Yields:
      A dictionary of JSON data.
    """
    if agent_name not in self.remote_agent_connections:
      raise ValueError(f"Agent {agent_name} not found")
    state = tool_context.state
    state['agent'] = agent_name
    card = self.cards[agent_name]
    client = self.remote_agent_connections[agent_name]
    if not client:
      raise ValueError(f"Client not available for {agent_name}")
    if 'task_id' in state:
      taskId = state['task_id']
    else:
      taskId = str(uuid.uuid4())
    sessionId = state['session_id']
    task: Task
    messageId = ""
    metadata = {}
    if 'input_message_metadata' in state:
      metadata.update(**state['input_message_metadata'])
      if 'message_id' in state['input_message_metadata']:
        messageId = state['input_message_metadata']['message_id']
    if not messageId:
      messageId = str(uuid.uuid4())
    metadata.update(**{'conversation_id': sessionId, 'message_id': messageId})
    request: TaskSendParams = TaskSendParams(
        id=taskId,
        sessionId=sessionId,
        message=Message(
            role="user",
            parts=[TextPart(text=message)],
            metadata=metadata,
        ),
        acceptedOutputModes=["text", "text/plain", "image/png"],
        # pushNotification=None,
        metadata={'conversation_id': sessionId},
    )
    task = await client.send_task(request, self.task_callback)


    # Check if a valid task with status was returned before accessing attributes
    if task and task.status:
      # Assume completion unless a state returns that isn't complete
      state['session_active'] = task.status.state not in [
          TaskState.COMPLETED,
          TaskState.CANCELED,
          TaskState.FAILED,
          TaskState.UNKNOWN,
      ]
      if task.status.state == TaskState.INPUT_REQUIRED:
        # Force user input back
        tool_context.actions.skip_summarization = True
        tool_context.actions.escalate = True
      elif task.status.state == TaskState.CANCELED:
        # Open question, should we return some info for cancellation instead
        raise ValueError(f"Agent {agent_name} task {task.id} is cancelled")
      elif task.status.state == TaskState.FAILED:
        # Raise error for failure
        raise ValueError(f"Agent {agent_name} task {task.id} failed")
    else:
      # Handle the case where task or task.status is None (e.g., log a warning or raise an error)
      print(f"Warning: Received invalid task object or status from {agent_name}. Task: {task}", file=sys.stderr)
      # Decide how to proceed: maybe assume session is inactive or raise a more specific error
      state['session_active'] = False
      # Depending on requirements, you might want to raise an error here instead of just returning []

    response = []

    # Also check task and task.status before accessing message/artifacts
    if task and task.status and task.status.message:
      # Assume the information is in the task message.
      response.extend(convert_parts(task.status.message.parts, tool_context))
    if task and task.artifacts:
      for artifact in task.artifacts:
        response.extend(convert_parts(artifact.parts, tool_context))
    return response

def convert_parts(parts: list[Part], tool_context: ToolContext):
  rval = []
  for p in parts:
    rval.append(convert_part(p, tool_context))
  return rval

def convert_part(part: Part, tool_context: ToolContext):
  if part.type == "text":
    return part.text
  elif part.type == "data":
    return part.data
  elif part.type == "file":
    # Repackage A2A FilePart to google.genai Blob
    # Currently not considering plain text as files    
    file_id = part.file.name
    file_bytes = base64.b64decode(part.file.bytes)    
    file_part = types.Part(
      inline_data=types.Blob(
        mime_type=part.file.mimeType,
        data=file_bytes))
    tool_context.save_artifact(file_id, file_part)
    tool_context.actions.skip_summarization = True
    tool_context.actions.escalate = True
    return DataPart(data = {"artifact-file-id": file_id})
  return f"Unknown type: {p.type}"
