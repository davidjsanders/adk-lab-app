import logging
from app.classes.settings import Settings
from a2a_agent.models.platform import Platform

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)


def identify_platform() -> Platform:
    """Identify the platform the agent is running on."""
    return Platform.GOOGLE_CLOUD_AGENT_ENGINE
    # settings = Settings()
    # logger.debug("Identifying platform")
    # if settings.platform == Platform.GOOGLE_CLOUD_RUN:
    #     logger.debug("Platform is Google Cloud Run")
    #     return Platform.GOOGLE_CLOUD_RUN
    # elif settings.platform == Platform.GOOGLE_CLOUD_AGENT_ENGINE:
    #     logger.debug("Platform is Google Cloud Agent Engine")
    #     return Platform.GOOGLE_CLOUD_AGENT_ENGINE
    # else:
    #     logger.debug("Platform is custom")
    #     return Platform.CUSTOM