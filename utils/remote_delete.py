from vertexai import agent_engines
import os

ORCHESTRATE_AGENT_ID = os.environ.get('ORCHESTRATE_AGENT_ID')
agent_engine = agent_engines.get(ORCHESTRATE_AGENT_ID)


agent_engine = agent_engines.get(ORCHESTRATE_AGENT_ID)
agent_engine.delete(force=True)