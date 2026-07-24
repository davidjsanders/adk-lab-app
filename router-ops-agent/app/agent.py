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

"""Router Operations Agent combining MCP Tools, Dynamic Auth, Global Gemini, ADK Skills, and Subagents."""
import logging
logging.basicConfig(level=logging.INFO)

from google.adk.agents import Agent
from google.adk.apps import App

from app.classes.global_gemini import GlobalGemini
from app.config import settings
from app.helpers.callbacks import intercept_image_card_tool
from app.plugins.a2ui_plugin import A2UIPlugin
from app.subagents import diagnostic_agent, remediation_agent
from app.tools.mcp_tools import mcp_toolset

# Instantiate GlobalGemini model instance for coordinator
fast_model = GlobalGemini(model=settings.fast_model)
pro_model = GlobalGemini(model=settings.pro_model)

# Shared A2UI Plugin instance (preserved for plugin use)
a2ui_plugin = A2UIPlugin()

# ---------------------------------------------------------------------------
# Fleet Coordinator Root Agent & App Definition
# ---------------------------------------------------------------------------

root_agent = Agent(
    name="router_fleet_coordinator",
    model=fast_model,
    description="Primary orchestrator for router fleet operations. Coordinates triage, telemetry analysis, and remediation.",
    instruction="""
    You are the Router Fleet Operations Coordinator.
    You manage router fleet health, triage network anomalies, and direct remediation actions.
    
    CRITICAL Safeguard:
    - You have NO direct tools of your own to query routers, list the fleet, or execute remediation commands.
    - If the user asks for ANY fleet action, telemetry, logs, listing, or troubleshooting, you MUST delegate to the appropriate sub-agent using `transfer_to_agent`. Do NOT attempt to run tools yourself.
    
    Delegation & Routing Workflow:
    1. When asked to list the fleet, list routers, find routers, or show a summary of the fleet:
       - ALWAYS delegate the request to `diagnostic_agent`. Do NOT attempt to invoke `list_router_fleet` yourself.
    2. When asked to show, display, or render a router's status, LED status, card, or diagnostics (e.g. "show the card for RTR-CAN-EAST-02", "show the image card"):
       - ALWAYS delegate the request to `diagnostic_agent`. Do NOT attempt to invoke diagnostic tools yourself.
    3. For general diagnostic inquiry, status audits, or troubleshooting queries:
       - Delegate telemetry gathering to `diagnostic_agent`.
    4. If remediation is required (BGP reset, reboot, LED update), delegate action execution to `remediation_agent`.
    5. When a user action event or button click is received (e.g. `send_router_command` or power/reboot toggle):
       - Immediately delegate executing the command and card refresh to `remediation_agent` or `diagnostic_agent`.
    
    Verbatim Relay Rule:
    - If any sub-agent returns a response starting with `<a2ui-json>` and ending with `</a2ui-json>`, you MUST relay that entire block to the user verbatim.
    - Do NOT include any leading or trailing text, explanations, or introductory sentences.
    """,
    tools=[],
    sub_agents=[
        diagnostic_agent,
        remediation_agent,
    ],
    # after_tool_callback=intercept_image_card_tool,
)

app = App(
    root_agent=root_agent,
    name="app",
    plugins=[a2ui_plugin],
)
