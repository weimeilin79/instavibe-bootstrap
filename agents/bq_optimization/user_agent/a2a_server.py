import os
import logging
from dotenv import load_dotenv

# Assuming the a2a_common wheel will be installed and available in PYTHONPATH
from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill
from common.task_manager import AgentTaskManager # Using AgentTaskManager

# Import the root_agent from agent.py
from .agent import root_agent # This is BigQueryUserAgent

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables for the server
A2A_HOST = os.environ.get("BQ_USER_AGENT_A2A_HOST", "0.0.0.0") # Specific host for this agent
A2A_PORT = int(os.environ.get("BQ_USER_AGENT_A2A_PORT", 10005)) # Specific port
PUBLIC_URL = os.environ.get("BQ_USER_AGENT_PUBLIC_URL") # Specific public URL

def main():
    try:
        if not PUBLIC_URL:
            logger.warning("BQ_USER_AGENT_PUBLIC_URL environment variable is not set. Agent card URL will be incomplete.")
            # Provide a default or handle as appropriate
            effective_public_url = f"http://{A2A_HOST}:{A2A_PORT}"
        else:
            effective_public_url = PUBLIC_URL

        capabilities = AgentCapabilities(streaming=False) # Adjust as needed

        # Define a skill for the BigQueryUserAgent
        skill = AgentSkill(
            id="bq_optimization_request_handler",
            name="BigQuery Optimization Request Handler",
            description="Receives user requests for BigQuery optimization and forwards them to a specialized lens agent.",
            tags=["bigquery", "optimization"],
            examples=["Can you help optimize my BigQuery query?", "I need advice on my BigQuery costs."]
        )

        agent_card = AgentCard(
            name="BigQuery User Agent",
            description="Front-facing agent to handle user requests for BigQuery optimization.",
            url=effective_public_url, # URL where this agent is accessible
            version="1.0.0",
            # Assuming root_agent (LlmAgent) has these attributes or they are handled by AgentTaskManager
            # defaultInputModes=root_agent.SUPPORTED_CONTENT_TYPES if hasattr(root_agent, 'SUPPORTED_CONTENT_TYPES') else ["text/plain"],
            # defaultOutputModes=root_agent.SUPPORTED_CONTENT_TYPES if hasattr(root_agent, 'SUPPORTED_CONTENT_TYPES') else ["text/plain"],
            defaultInputModes=["text/plain"], # Basic text input
            defaultOutputModes=["text/plain"], # Basic text output
            capabilities=capabilities,
            skills=[skill]
        )

        # Ensure root_agent is compatible with AgentTaskManager.
        # The PlannerAgent in the example is directly instantiated.
        # If root_agent is an LlmAgent instance, it should work if AgentTaskManager expects an ADK agent.
        task_manager = AgentTaskManager(agent=root_agent)

        server = A2AServer(
            agent_card=agent_card,
            task_manager=task_manager,
            host=A2A_HOST,
            port=A2A_PORT,
        )
        logger.info(f"Attempting to start BigQueryUserAgent A2A server with Agent Card: {agent_card.name} on {A2A_HOST}:{A2A_PORT}")
        server.start()

    except ImportError as e:
        logger.error(f"Failed to import common modules: {e}. Ensure a2a_common wheel is installed and in PYTHONPATH.")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup for BigQueryUserAgent: {e}", exc_info=True)
        exit(1)

if __name__ == "__main__":
    main()
