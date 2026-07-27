import logging
import os
from app.classes.settings import Settings
from a2a_agent.models.platform import Platform

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)


def identify_platform() -> Platform:
    """Identify the platform the agent is running on."""
    settings = Settings()
    logger.debug("Identifying platform")

    k_service = os.environ.get("K_SERVICE", "")

    # Check for Agent Engine / Runtime first
    if (
        "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY" in os.environ
        or os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID")
        or settings.google_cloud_agent_engine_id
        or k_service.startswith("reasoning-engine")
    ):
        logger.debug("Platform is Google Cloud Agent Engine")
        return Platform.GOOGLE_CLOUD_AGENT_ENGINE

    # Check for standalone Cloud Run
    if k_service:
        logger.debug("Platform is Google Cloud Run")
        return Platform.GOOGLE_CLOUD_RUN

    return Platform.CUSTOM