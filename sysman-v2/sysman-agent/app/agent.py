import logging
from google.adk.apps import App
from .classes.specialist_agent import SpecialistAgent
from .helpers.config import agent_config
from .plugins.a2ui_plugin import A2UIPlugin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sysman-agent.agent")

# Shared A2UI Plugin instance
a2ui_plugin = A2UIPlugin()

logger.info(f"Starting SysMan Agent in role: {agent_config.role}")

root_agent = SpecialistAgent(config=agent_config)
app = App(
    root_agent=root_agent,
    name="app",
    plugins=[a2ui_plugin],
)
