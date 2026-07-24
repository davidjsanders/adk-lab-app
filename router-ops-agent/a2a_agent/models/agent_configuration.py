from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from vertexai.preview.reasoning_engines import A2aAgent
from a2a_agent.models.platform import Platform


class AgentConfiguration(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True
    )

    agent: A2aAgent = Field(
        ...,
        description="A2A Agent to deploy."
    )
    agent_id: Optional[str] = Field(
        None,
        description="Agent ID for the deployed agent."
    )
    api_version: Optional[str] = Field(
        "v1beta1",
        description="API version to use for the agent.",
    )
    display_name: str = Field(
        "UnknownAgent",
        description="Display name of the agent.",
    )
    description: Optional[str] = Field(
        None,
        description="Description of the agent.",
    )
    env_path: Optional[str] = Field(
        ".env",
        description="Path to environment variables file.",
    )
    env_vars: Optional[Dict[str, str]] = Field(
        None,
        description="Environment variables for the agent.",
    )
    location: str = Field(
        ...,
        description="Google Cloud location (region)"
    )
    package_directories: list[str] = Field(
        default_factory=lambda: ["app", "a2a_agent"],
        description="Extra packages to install in the agent environment.",
    )
    platform: Platform = Field(
        ...,
        description="Platform to deploy the agent to."
    )
    project_id: str = Field(
        ...,
        description="Google Cloud Project ID"
    )
    requirements_path: Optional[str] = Field(
        "requirements.txt",
        description="Path to requirements file.",
    )
    service_account: Optional[str] = Field(
        None,
        description="Service account for deployed agent"
    )
    staging_bucket: str = Field(
        ...,
        description="Staging bucket for the agent.",
    )
    