# ruff: noqa
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

import structlog
from pathlib import Path

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from .helpers.logger import configure_logger
from .tools.network_ops import execute_bgp_soft_reset


# Set up logging
configure_logger()
logger = structlog.getLogger(__name__)
if hasattr(logger, "setLevel"):
    logger.setLevel(logging.DEBUG)

# Set up system instructions
system_instructions: str | None = None
instructions_path = Path(__file__).parent / "config" / "system_instructions.md"
try:
    with open(instructions_path, "r") as f:
        system_instructions = f.read()
    logger.info("Loaded system instructions")
except FileNotFoundError as fnfe_error:
    logger.error(
        "Could not load system instructions from "
        f"{instructions_path}: "
        f"{fnfe_error}"
    )
    system_instructions = (
        "You must report that there has been an error in "
        "loading the system instructions and that you cannot "
        "fulfill the user's request at this time."
    )

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=system_instructions,
    tools=[
        execute_bgp_soft_reset
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
