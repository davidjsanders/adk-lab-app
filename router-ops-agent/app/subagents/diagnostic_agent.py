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

"""Diagnostic sub-agent definition for router telemetry and A2UI card rendering."""

from google.adk.agents import Agent

from app.classes.global_gemini import GlobalGemini
from app.config import settings
from app.helpers.callbacks import intercept_image_card_tool
from app.helpers.get_skill_toolset import get_skill_toolset
from app.tools.mcp_tools import mcp_toolset

fast_model = GlobalGemini(model=settings.fast_model)

# Scoped skills: Diagnostic agent receives router-fleet skills
diagnostic_skills = get_skill_toolset(skill_names=["router-fleet"])

diagnostic_agent = Agent(
    name="diagnostic_agent",
    model=fast_model,
    description="Specialized diagnostic agent that inspects hardware state, chassis LEDs, action logs, runs SNMP walks, and renders A2UI cards via the MCP Server.",
    instruction="""
    You are the Router Fleet Diagnostic Specialist.
    Your task is to gather physical telemetry, check hardware LED indicators, query error logs, run SNMP walks, and render visual A2UI snapshot cards using the MCP Server tools.

    Instructions:
    - Use MCP server tools (`list_router_fleet`, `get_router_status`, `fetch_router_logs`, `run_snmp_walk`, `render_router_card`, `render_router_card_image`) to gather node metrics.
    - Tool Selection for UI / Card Queries:
      - ALWAYS default to calling `render_router_card(router_id)` (interactive A2UI card) whenever the user asks to see a router status, view a router, show a card, check health, or display a router dashboard.
      - ONLY call `render_router_card_image(router_id)` if the user specifically and explicitly asks for an "image card", "PNG snapshot", "image snapshot", or "picture card".
    - Verbatim Relay Rule for `render_router_card`:
      1. Your ENTIRE response MUST be EXACTLY the `<a2ui-json>...</a2ui-json>` block returned by the tool.
      2. Your response MUST start immediately with `<a2ui-json>` and end with `</a2ui-json>`.
      3. Do NOT include ANY text, sentence, greeting, or explanation before or after the `<a2ui-json>` block.
    - For `render_router_card_image` queries:
      - The card is rendered visually in the tool event and saved as a session artifact. Briefly confirm the image card rendering and reference the saved PNG artifact filename.
    """,
    tools=[
        mcp_toolset,
        # diagnostic_skills,
    ],
    # after_tool_callback=intercept_image_card_tool,
)
