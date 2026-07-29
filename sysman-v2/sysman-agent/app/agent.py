import logging
import os
from google.adk.apps import App
from app.classes.orchestrator import Orchestrator
from app.classes.specialist import SpecialistAgent
from app.config import settings
from app.plugins.a2ui_plugin import A2UIPlugin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sysman-agent.agent")

# Shared A2UI Plugin instance
a2ui_plugin = A2UIPlugin()

# Resolve Agent Role
agent_role = settings.agent_role.strip().capitalize()  # 'Orchestrator', 'Jira', 'Confluence', 'Linux'
logger.info(f"Starting SysMan Agent in role: {agent_role}")

if agent_role == "Orchestrator":
    root_agent = Orchestrator()

else:
    agent_categories = [c.strip() for c in settings.agent_categories.split(",") if c.strip()]
    root_agent = SpecialistAgent(role=agent_role, categories=agent_categories)

app = App(
    root_agent=root_agent,
    name="app",
    plugins=[a2ui_plugin],
)
