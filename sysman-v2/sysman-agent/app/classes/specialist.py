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

"""Specialist agent class loading configuration and instructions from JSON resources."""

import json
import os
from google.adk.agents import Agent
from app.classes.global_gemini import GlobalGemini
from app.config import settings
from app.helpers.get_skill_toolset import get_skill_toolset
from app.tools.mcp_tools import mcp_toolset


class SpecialistAgent(Agent):
    """Generic Specialist Agent that loads its target system and instructions dynamically from config."""

    def __init__(self, role: str, categories: list[str]):
        """Initializes a SpecialistAgent by loading its metadata and instructions from config.

        Args:
            role: The agent role string (e.g. 'Jira', 'Confluence', 'Linux').
            categories: List of system categories matching this agent.
        """
        # 1. Load instructions and system config from JSON
        config_path = os.path.join(os.path.dirname(__file__), "..", "resources", "agents_config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        if role not in config:
            raise ValueError(f"Agent role '{role}' is not defined in agent configuration.")

        agent_cfg = config[role]
        target_system_id = agent_cfg["target_system_id"]
        description = agent_cfg["description"]
        instruction_template = agent_cfg["instruction"]

        # Populate instruction templates
        instruction = instruction_template.replace("{target_system_id}", target_system_id)

        # 2. Load dynamically filtered skills matching this agent type and categories
        system_skills = get_skill_toolset(agent_type=role, categories=categories)

        # 3. Initialize the ADK Agent
        super().__init__(
            name=f"sysman_{role.lower()}_agent",
            model=GlobalGemini(model=settings.fast_model),
            description=description,
            instruction=instruction,
            tools=[
                mcp_toolset,
                system_skills,
            ],
        )
