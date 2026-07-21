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

"""Remediation sub-agent definition for router state changes and hardware actions."""

from google.adk.agents import Agent

from app.classes.global_gemini import GlobalGemini
from app.config import settings
from app.helpers.callbacks import intercept_image_card_tool
from app.helpers.get_skill_toolset import get_skill_toolset
from app.tools.mcp_tools import mcp_toolset

pro_model = GlobalGemini(model=settings.pro_model)

# Scoped skills: Remediation agent receives policy-based routing & routing metrics
remediation_skills = get_skill_toolset(
    skill_names=["policy-based-routing", "routing-metrics"]
)

remediation_agent = Agent(
    name="remediation_agent",
    model=pro_model,
    description="High-reasoning remediation specialist executing BGP resets, chassis reboots, fault tests, and LED overrides via the MCP Server.",
    instruction="""
    You are the Router Hardware Remediation Specialist.
    You carry out hardware state modifications, BGP peering resets, chassis reboots, and LED overrides via MCP Server tools.

    Instructions:
    - High-stakes actions (`reset_bgp_session`, `reboot_router`, `inject_bgp_fault`, `send_router_command`) require explicit human confirmation.
    - Clearly present the target router ID and proposed action before execution.
    - Use `set_router_led` to set chassis indicators (e.g. amber for maintenance mode).
    - After any successful remediation action, you MUST call `render_router_card(router_id)` to refresh the UI.
    - Your response with the card MUST be EXACTLY the `<a2ui-json>...</a2ui-json>` block returned by the tool, with NO other text.
    """,
    tools=[
        mcp_toolset,
        # remediation_skills,
    ],
    # after_tool_callback=intercept_image_card_tool,
)
