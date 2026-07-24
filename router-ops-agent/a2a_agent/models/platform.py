from enum import Enum

class Platform(str, Enum):
    GOOGLE_CLOUD_RUN = "google_cloud_run"
    GOOGLE_CLOUD_AGENT_ENGINE = "google_cloud_agent_engine"
    CUSTOM = "custom"
