# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Application settings class loaded from environment variables."""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings class loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Logging
    log_level: str = Field(
        default=os.environ.get("LOG_LEVEL", "INFO").upper(),
        validation_alias="LOG_LEVEL"
    )
    log_format: str = Field(
        default="%(asctime)s, %(levelname)s, %(module)s.%(funcName)s: %(message)s",
        validation_alias="LOG_FORMAT"
    )

    # Agent configuration
    agent_version: str = Field(
        default=os.environ.get("AGENT_VERSION", "0.1.0"),
        validation_alias="AGENT_VERSION"
    )
    agent_endpoint: Optional[str] = Field(
        default=os.environ.get("AGENT_ENDPOINT", None),
        validation_alias="AGENT_ENDPOINT"
    )

    # GCP and Vertex AI Configuration
    google_cloud_project: str = Field(
        default="agentspace-argolis-demo",
        validation_alias="GOOGLE_CLOUD_PROJECT"
    )
    google_cloud_location: str = Field(
        default="us-central1",
        validation_alias="GOOGLE_CLOUD_LOCATION"
    )
    google_genai_use_vertexai: bool = Field(
        default=True,
        validation_alias="GOOGLE_GENAI_USE_VERTEXAI"
    )
    artifact_storage_bucket: str = Field(
        default="",
        validation_alias="ARTIFACT_STORAGE_BUCKET"
    )
    google_cloud_agent_engine_id: Optional[str] = Field(
        default=os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID", None),
        validation_alias="GOOGLE_CLOUD_AGENT_ENGINE_ID"
    )
    google_cloud_run_service_name: Optional[str] = Field(
        default=os.environ.get("K_SERVICE", None),
        validation_alias="GOOGLE_CLOUD_RUN_SERVICE_NAME"
    )
    google_cloud_run_revision: Optional[str] = Field(
        default=os.environ.get("K_REVISION", None),
        validation_alias="GOOGLE_CLOUD_RUN_REVISION"
    )

    # Service Account Impersonation
    impersonate_sa: str = Field(
        default="",
        validation_alias="IMPERSONATE_SA"
    )

    # Fleet Infrastructure URLs
    mcp_server_url: str = Field(
        default="https://router-mcp-server-63466983700.us-central1.run.app",
        validation_alias="MCP_SERVER_URL",
    )

    # Model Configuration
    fast_model: str = Field(
        default="gemini-3-flash-preview",
        validation_alias="FAST_MODEL"
    )
    pro_model: str = Field(
        default="gemini-3.1-pro-preview",
        validation_alias="PRO_MODEL"
    )

    # Alias properties
    @property
    def project_id(self) -> str:
        """Alias for google_cloud_project."""
        return self.google_cloud_project

    @property
    def location(self) -> str:
        """Alias for google_cloud_location."""
        return self.google_cloud_location
