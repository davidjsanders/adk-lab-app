# if os.environ.get("K_SERVICE") or os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID"):
#     try:
#         import OpenSSL.SSL
#         OpenSSL.SSL.Context._require_not_used = lambda self: None
#     except (ImportError, AttributeError):
#         pass

import logging
import warnings

from google.adk import __version__ as ADK_VERSION
from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService
from google.adk.auth.credential_service.session_state_credential_service import (
    SessionStateCredentialService,
)
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from app.agent import app as adk_app
from app.classes.settings import Settings

from a2a_agent.classes.flexible_vertex_ai_session_service import FlexibleVertexAiSessionService

logger = logging.getLogger(__name__)

async def create_runner() -> Runner:
    """
    Create a Runner for the ADK Agent
    """
    settings = Settings()
    warnings.filterwarnings('ignore', message=r'.*EXPERIMENTAL.*')

    # Resolve log level dynamically from environment
    log_level_str = settings.log_level
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Force log format and level for remote execution
    formatter = logging.Formatter(settings.log_format)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(log_level)

    # Set all loggers
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    root_logger.addHandler(handler)

    # Also set specific loggers just in case
    logging.getLogger("app").setLevel(log_level)
    logging.getLogger("google_adk").setLevel(log_level)

    logger.info(
        "=== Starting A2A Search Assistant Agent App (Version: %s) [ADK Version: %s] ===",
        settings.agent_version,
        ADK_VERSION
    )

    bucket_name = settings.artifact_storage_bucket
    artifact_service = (
        GcsArtifactService(bucket_name=bucket_name)
        if bucket_name
        else InMemoryArtifactService()
    )

    ae_id = settings.google_cloud_agent_engine_id
    if ae_id and ae_id != "test-agent-engine":
        logger.info(f"Using Vertex AI Session Service (Flexible) for Agent Engine ID: {ae_id}")
        session_service = FlexibleVertexAiSessionService(
            project=settings.project_id,
            location=settings.location,
            agent_engine_id=ae_id,
        )
    else:
        logger.info("Using local InMemorySessionService")
        session_service = InMemorySessionService()

    return Runner(
        app=adk_app,
        session_service=session_service,
        artifact_service=artifact_service,
        credential_service=SessionStateCredentialService(),
    )
