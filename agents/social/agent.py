import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import LoopAgent, LlmAgent, BaseAgent
from social.instavibe import get_person_posts,get_person_friends,get_person_id_by_name,get_person_attended_events
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from typing import AsyncGenerator
import logging

from google.genai import types # For types.Content
from google.adk.agents.callback_context import CallbackContext
from typing import Optional

# Get a logger instance
log = logging.getLogger(__name__)

# Define the tools
# This assumes these functions are directly usable as tools or have been
# decorated/wrapped appropriately elsewhere if needed by LlmAgent.
# Also ensure these functions are compatible with LlmAgent tool requirements.
# For example, they might need type hints or specific return structures.
social_tools = [
    get_person_posts,
    get_person_friends,
    get_person_id_by_name,
    get_person_attended_events
]

# Define the root_agent
root_agent = LlmAgent(
    model='gemini-pro', # Or another appropriate model
    name='social_agent_from_llm', # Renamed to avoid conflict
    instruction="""\
You are the Instavibe Social Agent.
Your goal is to help users get information about people, their posts, friends, and events using the available tools.
- Use `get_person_posts` to find posts by a person.
- Use `get_person_friends` to find friends of a person.
- Use `get_person_id_by_name` to get a person's ID if you only have their name.
- Use `get_person_attended_events` to find events a person has attended.
Be helpful and use the tools as needed to answer user queries.
""",
    tools=social_tools
)

log.info("Social agent 'root_agent' initialized with LlmAgent.")
