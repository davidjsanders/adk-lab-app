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

"""Sysman agent entrypoint module for initializing and starting the agent app."""

import logging
import logging_config
from google.adk.apps import App
from .classes.specialist_agent import SpecialistAgent
from .helpers.config import agent_config
from .plugins.a2ui_plugin import A2UIPlugin

logging_config.setup_logging()
logger = logging.getLogger("sysman-agent.agent")

# Shared A2UI Plugin instance for handling A2UI Components
a2ui_plugin = A2UIPlugin()

# Initialize the root agent (depends on role)
logger.info(f"Starting SysMan Agent in role: {agent_config.role}")
root_agent = SpecialistAgent(config=agent_config)

# Initialize the App
app = App(
    root_agent=root_agent,
    name="app",
    plugins=[a2ui_plugin],
)
