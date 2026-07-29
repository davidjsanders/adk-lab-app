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

"""Pydantic model classes for resolving remote sub-agents."""

from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from pydantic import BaseModel, ConfigDict, Field


class AgentSpec(BaseModel):
    """Specification configuration for resolving a remote sub-agent."""

    key: str = Field(description="Internal lookup dictionary key for the resolved agent")
    name: str = Field(description="Unique name for the remote agent instance")
    registry_id: str = Field(description="Name pattern of the agent registered in the cloud Agent Registry")
    description: str = Field(description="Fallback description used when creating the remote agent statically")
    static_url: str = Field(description="Fallback direct A2A connection URL")
