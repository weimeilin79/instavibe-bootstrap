import os
import logging
from dotenv import load_dotenv

from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill
from common.task_manager import AgentTaskManager

# Import the root_agent from agent.py. It should be fully initialized.
from .agent import root_agent as bigquery_lens_agent # Alias for clarity

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

A2A_HOST = os.environ.get("BQ_LENS_AGENT_A2A_HOST", "0.0.0.0")
A2A_PORT = int(os.environ.get("BQ_LENS_AGENT_A2A_PORT", 10006))
PUBLIC_URL = os.environ.get("BQ_LENS_AGENT_PUBLIC_URL")

def main():
    try:
        if not PUBLIC_URL:
            logger.warning("BQ_LENS_AGENT_PUBLIC_URL environment variable is not set. Agent card URL will be incomplete.")
            effective_public_url = f"http://{A2A_HOST}:{A2A_PORT}"
        else:
            effective_public_url = PUBLIC_URL

        capabilities = AgentCapabilities(streaming=False)

        skill = AgentSkill(
            id="bq_optimization_analyzer",
            name="BigQuery Optimization Analyzer",
            description="Analyzes BigQuery queries using specialized tools and provides optimization recommendations.",
            tags=["bigquery", "optimization", "analysis"],
            examples=["Analyze query: SELECT * FROM table", "Provide cost saving tips for my BigQuery project"]
        )

        agent_card = AgentCard(
            name="BigQuery Lens Agent",
            description="Specialized agent for BigQuery optimization analysis.",
            url=effective_public_url,
            version="1.0.0",
            defaultInputModes=["text/plain"],
            defaultOutputModes=["text/plain"],
            capabilities=capabilities,
            skills=[skill]
        )

        # The bigquery_lens_agent imported from .agent should now have its tools initialized at module load time.
        task_manager = AgentTaskManager(agent=bigquery_lens_agent)

        server = A2AServer(
            agent_card=agent_card,
            task_manager=task_manager,
            host=A2A_HOST,
            port=A2A_PORT,
        )
        logger.info(f"Attempting to start BigQueryLensAgent A2A server with Agent Card: {agent_card.name} on {A2A_HOST}:{A2A_PORT}")
        logger.info(f"BigQueryLensAgent tools: {[tool.name for tool in bigquery_lens_agent.tools] if bigquery_lens_agent.tools else 'No tools loaded'}")
        server.start()

    except ImportError as e:
        logger.error(f"Failed to import common modules: {e}. Ensure a2a_common wheel is installed and in PYTHONPATH.")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup for BigQueryLensAgent: {e}", exc_info=True)
        exit(1)

if __name__ == "__main__":
    main()
