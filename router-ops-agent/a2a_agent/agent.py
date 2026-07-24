# Prevent ValueError: Context has already been used to create a Connection (PyOpenSSL concurrency bug)
# only when running in the remote Reasoning Engine container (Cloud Run / Agent Engine).

# if os.environ.get("K_SERVICE") or os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID"):
#     try:
#         import OpenSSL.SSL
#         OpenSSL.SSL.Context._require_not_used = lambda self: None
#     except (ImportError, AttributeError):
#         pass
import asyncio
import logging

from a2a.types import (
    AgentCapabilities,
    AgentExtension,
    OpenIdConnectSecurityScheme,
    SecurityScheme,
    TransportProtocol,
)
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
from vertexai.preview.reasoning_engines import A2aAgent

from app.agent import app as adk_app
from app.classes.settings import Settings
from app.helpers.instructions import DESCRIPTION

from .helpers.executor_builder import executor_builder
from .helpers.task_store_builder import task_store_builder
from .helpers.identify_platform import identify_platform
from .helpers.metadata import get_instance_region, get_project_number
from .models.platform import Platform

# from app.tools.registry import get_skills
# from app.classes.config import CONFIG

# Global variable to hold the agent card
logger = logging.getLogger(__name__)

def get_a2a_agent() -> A2aAgent:
    settings = Settings()

    root_agent = adk_app.root_agent
    root_agent.description = DESCRIPTION

    builder = AgentCardBuilder(
        agent=root_agent,
        agent_version=settings.agent_version,
    )

    url = ""
    match identify_platform():
        case Platform.GOOGLE_CLOUD_RUN:
            svc = settings.google_cloud_run_service_name
            project_number = get_project_number()
            region = get_instance_region()
            url = f"https://{svc}-{project_number}.{region}.run.app/"
        case Platform.GOOGLE_CLOUD_AGENT_ENGINE:
            project = settings.google_cloud_project # or get_project_number()
            region = settings.google_cloud_location
            ae_id = settings.google_cloud_agent_engine_id
            url = (
                f"https://{region}-aiplatform.googleapis.com/v1beta1/"
                f"projects/{project}/locations/{region}/reasoningEngines/"
                f"{ae_id}/"
            )
        case Platform.CUSTOM:
            url = settings.agent_endpoint or "http://localhost:8001/"
            

    agent_card = asyncio.run(builder.build())
    agent_card.preferred_transport = TransportProtocol.http_json
    agent_card.url = url
    agent_card.capabilities = AgentCapabilities(
        streaming=True,
        extensions=[
            AgentExtension(
                uri="https://a2ui.org/a2a-extension/a2ui/v0.8",
                description="Ability to render A2UI",
                params={
                    "supportedCatalogIds": [
                        "https://a2ui.org/specification/v0_8/standard_catalog_definition.json"
                    ]
                },
            ),
            AgentExtension(
                uri="https://google.github.io/adk-docs/a2a/a2a-extension/",
                description=("Ability to use the new agent executor implementation"),
            ),
        ]
    )
    return A2aAgent(
        agent_card=agent_card,
        agent_executor_builder=executor_builder,
        task_store_builder=task_store_builder
    )

A2A_AGENT = get_a2a_agent()