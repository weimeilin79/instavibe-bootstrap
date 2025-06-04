from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill
from common.task_manager import AgentTaskManager
from planner.planner_agent import PlannerAgent
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host=os.environ.get("A2A_HOST", "localhost")
port=int(os.environ.get("A2A_PORT",10003))
PUBLIC_URL=os.environ.get("PUBLIC_URL")

def main():
    try:
        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id="night_out_planner",
            name="Night out planner",
            description="""
            This agent generates multiple fun plan suggestions tailored to your specified location, dates, and interests,
            all designed for a moderate budget. It delivers detailed itineraries,
            including precise venue information (name, latitude, longitude, and description), in a structured JSON format.
            """,
            tags=["instavibe"],
            examples=["What about Bostona MA this weekend?"],
        )
        agent_card = AgentCard(
            name="NightOut Planner Agent",
            description="""
            This agent generates multiple fun plan suggestions tailored to your specified location, dates, and interests,
            all designed for a moderate budget. It delivers detailed itineraries,
            including precise venue information (name, latitude, longitude, and description), in a structured JSON format.
            """,
            url=f"{PUBLIC_URL}",
            version="1.0.0",
            defaultInputModes=PlannerAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=PlannerAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=PlannerAgent()),
            host=host,
            port=port,
        )
        logger.info(f"Attempting to start server with Agent Card: {agent_card.name}")
        logger.info(f"Server object created: {server}")

        server.start()
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)

if __name__ == "__main__":
    main()