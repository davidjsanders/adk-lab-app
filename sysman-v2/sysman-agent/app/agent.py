import logging
import os
from google.adk.apps import App
from app.classes.orchestrator import Orchestrator
from app.classes.specialist_agent import SpecialistAgent
from app.helpers.config import settings, agent_config
from app.plugins.a2ui_plugin import A2UIPlugin

from .models.agent_roles import AgentRoles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sysman-agent.agent")

# Shared A2UI Plugin instance
a2ui_plugin = A2UIPlugin()

# Resolve Agent Role

logger.info(f"Starting SysMan Agent in role: {agent_config.role}")

match agent_config.role:
    case AgentRoles.ORCHESTRATOR:
        root_agent = Orchestrator()
    case AgentRoles.SPECIALIST:
        root_agent = SpecialistAgent(config=agent_config)
    case _:
        raise ValueError("Unsupported agent type")

app = App(
    root_agent=root_agent,
    name="app",
    plugins=[a2ui_plugin],
)
