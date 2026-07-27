import logging
from app.classes.settings import Settings
from a2a_agent.models.platform import Platform

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)


def identify_platform() -> Platform:
    """Identify the platform the agent is running on."""
    settings = Settings()
    logger.debug("Identifying platform")

    # Important note. Agent Runtime hosts Docker containers on managed
    # Cloud Run infrastructure. Because of this, Google Cloud sets the 
    # environment variable K_SERVICE 
    # (e.g. reasoning-engine-3409244159372951552-865571129717) 
    # inside the container for both standalone Cloud Run and Agent Runtime.
    # So, we need to check for Agent Runtime first.
    if os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID") or settings.google_cloud_agent_engine_id:
        logger.debug("Platform is Google Cloud Agent Engine")
        return Platform.GOOGLE_CLOUD_AGENT_ENGINE
    elif os.environ.get("K_SERVICE") or settings.google_cloud_run_service_name:
        logger.debug("Platform is Google Cloud Run")
        return Platform.GOOGLE_CLOUD_RUN
    else:
        logger.debug("Platform is custom")
        return Platform.CUSTOM