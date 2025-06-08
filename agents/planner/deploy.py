from google.adk.agents import LoopAgent # Changed from PlannerAgent
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import ReasoningEngine

# TODO: Confirm the correct agent object to use.
# agents/planner/planner_agent.py imports LoopAgent.
# We are assuming LoopAgent is the base class to be used for deployment.
# If this is incorrect, this will need to be adjusted.
# For example, it might be necessary to instantiate an agent object if planner_agent.py defines factory function
# or if another class from planner_agent.py is the main agent class.

# Placeholder for the actual agent object.
# This might need to be:
# from agents.planner.planner_agent import some_specific_agent_instance # if an instance is exported
# or:
# from agents.planner.planner_agent import create_some_agent # if a factory function is exported
# planner_agent_obj = create_some_agent()
# For now, we'll assume LoopAgent can be instantiated directly.
try:
    # Attempt to import and instantiate LoopAgent directly
    # This is a common pattern but might need adjustment based on how planner_agent.py is structured
    # or if LoopAgent requires specific arguments.
    planner_agent_obj = LoopAgent()
except TypeError as e:
    # This might happen if LoopAgent requires arguments for its constructor
    # Or if LoopAgent is not meant to be instantiated directly here.
    # Further investigation of planner_agent.py and ADK documentation will be needed if this fails.
    print(f"Error: Could not instantiate LoopAgent. Please check its definition and usage. Details: {e}")
    raise

display_name = "Planner Agent"
description = "This agent is responsible for planning tasks and breaking them down into smaller steps."

print(f"Attempting to deploy {display_name}...")

# Deploy the agent to Vertex AI Agent Engine
# The ` ReasoningEngine.create` is used here as per the new Vertex AI SDK.
# `agent_engines.create` is from an older version and might be deprecated.
# We will use ReasoningEngine.create based on common practices for new deployments.
remote_agent = ReasoningEngine.create(
    planner_agent_obj, # The agent object to deploy
    requirements=[
        "google-cloud-aiplatform[adk,agent_engines]>=1.90.0",
        "google-adk==0.4.0",
        "python-dateutil==2.9.0.post0",
        "a2a_common-0.1.0-py3-none-any.whl",
        "deprecated==1.2.18",
        # Ensure the SDK is included, already covered by google-cloud-aiplatform[adk,agent_engines]
    ],
    display_name=display_name,
    description=description,
    # location="us-central1", # Optional: specify location
    # project="your-gcp-project-id", # Optional: specify project
    # staging_bucket="your-gcs-bucket-for-staging", # Optional: specify staging bucket
)

print(f"{display_name} deployed successfully: {remote_agent.name}")
print(f"View in console: {remote_agent.resource_name}")
