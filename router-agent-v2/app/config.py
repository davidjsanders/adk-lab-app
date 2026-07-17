"""Configuration management for Router Agent V2."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Explicitly load .env to populate os.environ for helpers like auth.py
load_dotenv(override=True)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Allow extra env vars but don't bind them
    )

    # GCP and Vertex AI Configuration
    google_cloud_project: str = Field(
        default="agentspace-argolis-demo", validation_alias="GOOGLE_CLOUD_PROJECT"
    )
    google_cloud_location: str = Field(
        default="us-central1", validation_alias="GOOGLE_CLOUD_LOCATION"
    )
    google_genai_use_vertexai: bool = Field(
        default=True, validation_alias="GOOGLE_GENAI_USE_VERTEXAI"
    )

    # Service Account Impersonation
    impersonate_sa: str = Field(default="", validation_alias="IMPERSONATE_SA")

    # Fleet Infrastructure URLs
    mcp_server_url: str = Field(
        default="https://router-mcp-server-63466983700.us-central1.run.app",
        validation_alias="MCP_SERVER_URL",
    )

    # Model Configuration
    fast_model: str = Field(
        default="gemini-3-flash-preview", validation_alias="FAST_MODEL"
    )
    pro_model: str = Field(default="gemini-3-pro-preview", validation_alias="PRO_MODEL")


# Global config instance
settings = Settings()
