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

from functools import partial
import json
import logging
import os
import pathlib

from google.adk.agents import Agent
from google.adk.tools.skill_toolset import SkillToolset

from app.callbacks.specialist_state_loader import specialist_state_loader
from app.classes.global_gemini import GlobalGemini
from app.config import settings
from app.classes.skills_cache import SkillCache
# from app.tools.mcp_tools import mcp_toolset
from ..models.agent_categories import AgentCategories
from ..models.specialist_agent_config import SpecialistAgentConfig
from .mcp_helper import McpHelper
from .skills_helper import SkillsHelper


# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)


class SpecialistAgent(Agent):
    """Generic Specialist Agent that loads its target system and instructions dynamically from config."""

    def __init__(self, config: SpecialistAgentConfig):
        """Initialize a SpecialistAgent by loading its metadata and instructions from config.

        Args:
            config: SpecialistAgentConfig instance containing agent configuration.
        """
        agent_name = config.name.lower().replace(' ', '_')
        mcp_tools = []

        # 1. Get tools
        if config.mcp_servers:
            mcp_helper = McpHelper(
                settings=settings,
                mcp_servers=config.mcp_servers
            )
            mcp_tools = mcp_helper.get_toolset()

        # 2. Discover and fetch matching skills via the cache manager.
        system_skills = []
        if config.skills:
            skills_helper = SkillsHelper(
                settings=settings,
                skills=config.skills
            )
            system_skills = SkillToolset(skills=skills_helper.get_skills())

        # 3. Initialize the ADK Agent
        super().__init__(
            name=f"sysman_{agent_name}_agent",
            model=GlobalGemini(model=settings.fast_model),
            description=config.description,
            instruction=config.instruction,
            tools=[
                *mcp_tools,
                system_skills,
            ],
            before_agent_callback=partial(specialist_state_loader, target_systems=config.target_systems),
        )

