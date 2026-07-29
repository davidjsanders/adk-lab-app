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


class DiscoveredAgent(BaseModel):
    """Container model representing a resolved remote agent instance."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    key: str = Field(description="The internal key mapping for the agent")
    agent: RemoteA2aAgent = Field(description="The instantiated RemoteA2aAgent reference")
