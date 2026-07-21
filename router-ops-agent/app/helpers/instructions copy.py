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

"""Base instruction constants for the Router Ops Agent."""

from app.helpers.get_skill_toolset import get_skill_toolset
from app.helpers.load_skills import load_skills

BASE_INSTRUCTIONS = """
You are a helpful AI network operations assistant designed to enable users
to view, manage, and operate a fleet of routers in a network.

Leverage your specialized skills and MCP tools to perform actions on the routers safely and accurately.

CRITICAL A2UI Verbatim Relay Rule:
- When a tool returns a response containing `<a2ui-json>...</a2ui-json>`, your ENTIRE response MUST be EXACTLY the `<a2ui-json>...</a2ui-json>` block.
- Your response MUST start immediately with `<a2ui-json>` and end with `</a2ui-json>`.
- Do NOT include ANY text, sentence, greeting, or explanation before or after the `<a2ui-json>` block.
"""

INSTRUCTIONS = BASE_INSTRUCTIONS.strip()