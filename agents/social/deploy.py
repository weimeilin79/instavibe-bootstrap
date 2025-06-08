# Attempt to import the main agent object from agents.social.agent.
# The agents/social/agent.py file has several placeholders (e.g., #REPLACE FOR root_agent).
# We need to assume that a 'root_agent' or a similarly named main agent object
# will be available in that module once the placeholders are filled.
# For now, we will proceed with the assumption that 'root_agent' will be the object.
from agents.social import agent as social_agent_module # Alias to avoid confusion
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import ReasoningEngine

# Placeholder for the actual agent object.
# This will likely be 'social_agent_module.root_agent' once it's defined.
# If agents/social/agent.py defines agents differently (e.g., a factory function
# or a specific class to instantiate), this will need to be adjusted.
try:
    # Assuming root_agent will be directly accessible after imports.
    # This might require changes if 'root_agent' is initialized asynchronously
    # or needs to be instantiated.
    agent_obj = social_agent_module.root_agent
    if agent_obj is None: # Check if it's None due to placeholders
        raise AttributeError("'root_agent' is None. Ensure it is defined in agents/social/agent.py by replacing the placeholder.")
except AttributeError as e:
    print(f"Error: 'root_agent' not found in agents.social.agent. Please ensure the agent is defined and placeholders are filled. Details: {e}")
    # As a fallback, try to see if there's a SocialAgent class in social_agent.py to instantiate
    try:
        from agents.social.social_agent import SocialAgent
        agent_obj = SocialAgent()
        print("Fallback: Using SocialAgent from agents.social.social_agent.py")
    except Exception as fallback_e:
        print(f"Fallback failed: Could not instantiate SocialAgent. Details: {fallback_e}")
        raise e # Re-raise the original AttributeError
except Exception as e:
    print(f"An unexpected error occurred while trying to get the agent object: {e}")
    raise


display_name = "Social Agent"
description = "This agent handles social interactions, manages posts, and events for the Instavibe app."

print(f"Attempting to deploy {display_name}...")

# Deploy the agent to Vertex AI Agent Engine
remote_agent = ReasoningEngine.create(
    agent_obj,  # The agent object
    requirements=[
        "google-cloud-aiplatform", # Base SDK
        "google-cloud-spanner==3.54.0",
        "google-genai==1.14.0",
        "google-adk==0.4.0",
        "python-dotenv==1.1.0",
        "fastapi==0.115.12",
        "urllib3==2.4.0",
        "a2a_common-0.1.0-py3-none-any.whl",
        "deprecated==1.2.18",
    ],
    display_name=display_name,
    description=description,
)

print(f"{display_name} deployed successfully: {remote_agent.name}")
print(f"View in console: {remote_agent.resource_name}")
