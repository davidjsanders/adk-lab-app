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

"""Orchestrator agent class encapsulating routing instructions and sub-agent discovery."""

import json
import os
from google.adk.agents import Agent
from app.classes.global_gemini import GlobalGemini
from app.config import settings
from app.helpers.sub_agents import resolve_sub_agents
from app.models.sub_agents import AgentSpec
from ..models.specialist_agent_config import SpecialistAgentConfig


class Orchestrator(Agent):
    """Primary orchestrator for system management operations.

    Coordinates tasks and routes queries to specialized sub-agents.
    """

    def __init__(self, config: SpecialistAgentConfig):
        """Initializes the Orchestrator and dynamically resolves its sub-agents."""
        # 1. Load sub-agent specifications from JSON configuration
        config_path = os.path.join(os.path.dirname(__file__), "..", "resources", "orchestrator_config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            orchestrator_cfg = json.load(f)

        # TODO: Change this to a dynamic agent registry lookup
        specs = []
        for agent_cfg in orchestrator_cfg:
            static_url = os.getenv(agent_cfg["static_url_env_var"], agent_cfg["default_static_url"])
            specs.append(AgentSpec(
                key=agent_cfg["key"],
                name=agent_cfg["name"],
                registry_id=agent_cfg["registry_id"],
                description=agent_cfg["description"],
                static_url=static_url
            ))

        sub_agents = resolve_sub_agents(specs)

        # 2. Initialize parent class with configuration details
        super().__init__(
            name=config.name,
            model=GlobalGemini(model=settings.fast_model),
            description=config.description,
            instruction=config.instruction,
            tools=[],
            sub_agents=[da.agent for da in sub_agents],
        )
