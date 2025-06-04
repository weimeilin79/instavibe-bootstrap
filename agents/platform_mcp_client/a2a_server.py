from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill
from common.task_manager import AgentTaskManager
from platform_mcp_client.platform_agent import PlatformAgent

import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host=os.environ.get("A2A_HOST", "localhost")
port=int(os.environ.get("A2A_PORT",10002))
PUBLIC_URL=os.environ.get("PUBLIC_URL")

def main():
    try:
        capabilities = AgentCapabilities(streaming=True)
        skill = AgentSkill(
            id="instavibe_posting",
            name="Post social post and events on instavibe",
            description="""
            This "Instavibe" agent helps you create posts (identifying author, text, and sentiment – inferred if unspecified) and register
            for events (gathering name, date, attendee). It efficiently collects required information and utilizes dedicated tools
            to perform these actions on your behalf, ensuring a smooth sharing experience.
            """,
            tags=["instavibe"],
            examples=["Create a post for me, the post is about my cute cat and make it positive, and I'm Alice"],
        )
        agent_card = AgentCard(
            name="Instavibe Posting Agent",
            description="""
            This "Instavibe" agent helps you create posts (identifying author, text, and sentiment – inferred if unspecified) and register
            for events (gathering name, date, attendee). It efficiently collects required information and utilizes dedicated tools
            to perform these actions on your behalf, ensuring a smooth sharing experience.
            """,
            url=f"{PUBLIC_URL}",
            version="1.0.0",
            defaultInputModes=PlatformAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=PlatformAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=PlatformAgent()),
            host=host,
            port=port,
        )
        server.start()
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)

if __name__ == "__main__":
    main()