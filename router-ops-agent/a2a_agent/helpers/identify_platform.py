from app.classes.settings import Settings
from a2a_agent.models.platform import Platform

def identify_platform() -> Platform:
    """Identify the platform the agent is running on."""
    settings = Settings()
    if settings.google_cloud_run_service_name and settings.google_cloud_run_revision:
        return Platform.GOOGLE_CLOUD_RUN
    elif settings.google_cloud_agent_engine_id:
        return Platform.GOOGLE_CLOUD_AGENT_ENGINE
    else:
        return Platform.CUSTOM