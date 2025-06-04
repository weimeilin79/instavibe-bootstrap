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

class CheckCondition(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        #log.info(f"Checking status: {ctx.session.state.get("summary_status", "fail")}")
        log.info(f"Summary: {ctx.session.state.get("summary")}")

        status = ctx.session.state.get("summary_status", "fail").strip()
        is_done = (status == "completed")

        yield Event(author=self.name, actions=EventActions(escalate=is_done))

profile_agent = LlmAgent(
    name="profile_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to answer questions about the this person's social profile. User will ask person's profile using their name, make sure to fetch the id before getting other data."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about this person's social profile."
    ),
    tools=[get_person_posts,get_person_friends,get_person_id_by_name,get_person_attended_events],
)


summary_agent = LlmAgent(
    name="summary_agent",
    model="gemini-2.0-flash",
    description=(
        "Generate a comprehensive social summary as a single, cohesive paragraph. This summary should cover the activities, posts, friend networks, and event participation of one or more individuals. If multiple profiles are analyzed, the paragraph must also identify and integrate any common ground found between them."
    ),
    instruction=(
        """
        Your primary task is to synthesize social profile information into a single, comprehensive paragraph.

            **Input Scope & Default Behavior:**
            *   If specific individuals are named by the user, focus your analysis on them.
            *   **If no individuals are specified, or if the request is general, assume the user wants an analysis of *all relevant profiles available in the current dataset/context*.**

            **For each profile (whether specified or determined by default), you must analyze:**

            1.  **Post Analysis:**
                *   Systematically review their posts (e.g., content, topics, frequency, engagement).
                *   Identify recurring themes, primary interests, and expressed sentiments.

            2.  **Friendship Relationship Analysis:**
                *   Examine their connections/friends list.
                *   Identify key relationships, mutual friends (especially if comparing multiple profiles), and the general structure of their social network.

            3.  **Event Participation Analysis:**
                *   Investigate their past (and if available, upcoming) event participation.
                *   Note the types of events, frequency of attendance, and any notable roles (e.g., organizer, speaker).

            **Output Generation (Single Paragraph):**

            *   **Your entire output must be a single, cohesive summary paragraph.**
                *   **If analyzing a single profile:** This paragraph will detail their activities, interests, and social connections based on the post, friend, and event analysis.
                *   **If analyzing multiple profiles:** This paragraph will synthesize the key findings regarding posts, friends, and events for each individual. Crucially, it must then seamlessly integrate or conclude with an identification and description of the common ground found between them (e.g., shared interests from posts, overlapping event attendance, mutual friends). The aim is a unified narrative within this single paragraph.

            **Key Considerations:**
            *   Base your summary strictly on the available data.
            *   If data for a specific category (posts, friends, events) is missing or sparse for a profile, you may briefly acknowledge this within the narrative if relevant.
                """
        ),
    output_key="summary"
)

check_agent = LlmAgent(
    name="check_agent",
    model="gemini-2.0-flash",
    description=(
        "Check if everyone's social profile are summarized and has been generated. Output 'completed' or 'pending'."
    ),
    output_key="summary_status"
)

def modify_output_after_agent(callback_context: CallbackContext) -> Optional[types.Content]:

    agent_name = callback_context.agent_name
    invocation_id = callback_context.invocation_id
    current_state = callback_context.state.to_dict()
    current_user_content = callback_context.user_content
    print(f"[Callback] Exiting agent: {agent_name} (Inv: {invocation_id})")
    print(f"[Callback] Current summary_status: {current_state.get("summary_status")}")
    print(f"[Callback] Current Content: {current_user_content}")

    status = current_state.get("summary_status").strip()
    is_done = (status == "completed")
    # Retrieve the final summary from the state

    final_summary = current_state.get("summary")
    print(f"[Callback] final_summary: {final_summary}")
    if final_summary and is_done and isinstance(final_summary, str):
        log.info(f"[Callback] Found final summary, constructing output Content.")
        # Construct the final output Content object to be sent back
        return types.Content(role="model", parts=[types.Part(text=final_summary.strip())])
    else:
        log.warning("[Callback] No final summary found in state or it's not a string.")
        # Optionally return a default message or None if no summary was generated
        return None

root_agent = LoopAgent(
    name="InteractivePipeline",
    sub_agents=[
        profile_agent,
        summary_agent,
        check_agent,
        CheckCondition(name="Checker")
    ],
    description="Find everyone's social profile on events, post and friends",
    max_iterations=10,
    after_agent_callback=modify_output_after_agent
)
