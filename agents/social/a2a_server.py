from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill
from common.task_manager import AgentTaskManager
from social.social_agent import SocialAgent

import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host=os.environ.get("A2A_HOST", "localhost")
port=int(os.environ.get("A2A_PORT",10001))
PUBLIC_URL=os.environ.get("PUBLIC_URL")

def main():
    try:
        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id="social_profile_analysis",
            name="Analyze Instavibe social profile",
            description="""
            Using a provided list of names, this agent synthesizes Instavibe social profile information by analyzing posts, friends, and events.
            It delivers a comprehensive single-paragraph summary for individuals, and for groups, identifies commonalities in their social activities
            and connections based on profile data.
            """,
            tags=["instavibe"],
            examples=["Can you tell me about Bob and Alice?"],
        )
        agent_card = AgentCard(
            name="Social Profile Agent",
            description="""
            Using a provided list of names, this agent synthesizes Instavibe social profile information by analyzing posts, friends, and events.
            It delivers a comprehensive single-paragraph summary for individuals, and for groups, identifies commonalities in their social activities
            and connections based on profile data.
            """,
            url=f"{PUBLIC_URL}",
            version="1.0.0",
            defaultInputModes=SocialAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=SocialAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=SocialAgent()),
            host=host,
            port=port,
        )
        server.start()
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)

if __name__ == "__main__":
    main()