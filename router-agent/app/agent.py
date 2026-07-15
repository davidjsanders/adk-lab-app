"""Router Fleet Operations Multi-Agent Orchestrator.

Implements a multi-agent hierarchy for router fleet diagnostics, troubleshooting,
and hardware remediation using Google ADK 2.x and GlobalGemini models.
Integrates tools exclusively served over MCP from router-mcp-server with dynamic IAM auth.
"""

import logging

from google.adk import Agent
from google.adk.apps import App

from app.config import FAST_MODEL, PRO_MODEL
from app.helpers import GlobalGemini, intercept_image_card_tool
from app.tools import (
    mcp_toolset,
    search_troubleshooting_knowledge_base,
)

logger = logging.getLogger("router-agent.agent")

# Instantiate GlobalGemini model instances for regional location compatibility
fast_model_instance = GlobalGemini(model=FAST_MODEL)
pro_model_instance = GlobalGemini(model=PRO_MODEL)


# ---------------------------------------------------------------------------
# Specialized Sub-Agents
# ---------------------------------------------------------------------------

# 1. Telemetry & Diagnostic Specialist Agent (Powered by MCP Toolset)
router_diagnostic_agent = Agent(
    name="router_diagnostic_agent",
    model=fast_model_instance,
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
    ],
    after_tool_callback=intercept_image_card_tool,
)

# 2. Knowledge Grounding & SOP Search Specialist Agent
router_knowledge_agent = Agent(
    name="router_knowledge_agent",
    model=fast_model_instance,
    description="Specialized knowledge agent that searches operational manuals and SOPs for troubleshooting procedures.",
    instruction="""
You are the Router Knowledge Grounding Specialist.
Your job is to search troubleshooting manuals, knowledge bases, and standard operating procedures (SOPs) for hardware and network faults.

Instructions:
- Use `search_troubleshooting_knowledge_base` with specific error keywords (e.g. 'BGP peering down', 'Chassis overheat', 'packet loss').
- Synthesize recommended operational steps, severity ratings, and safety precautions.
- Provide step-by-step guidance back to the coordinator.
""",
    tools=[
        search_troubleshooting_knowledge_base,
    ],
)

# 3. Hardware Remediation Specialist Agent (Uses Gemini Pro & MCP Toolset for High-Reasoning Safeguards)
router_remediation_agent = Agent(
    name="router_remediation_agent",
    model=pro_model_instance,
    description="High-reasoning remediation specialist executing BGP resets, chassis reboots, fault tests, and LED overrides via the MCP Server.",
    instruction="""
You are the Router Hardware Remediation Specialist.
You carry out hardware state modifications, BGP peering resets, chassis reboots, and LED overrides via MCP Server tools.

Instructions:
- High-stakes actions (`reset_bgp_session`, `reboot_router`, `inject_bgp_fault`) require explicit human confirmation.
- Clearly present the target router ID and proposed action before execution.
- Use `set_router_led` to set chassis indicators (e.g. amber for maintenance mode).
- Provide a full summary of post-action system state following remediation.
""",
    tools=[
        mcp_toolset,
    ],
)

# ---------------------------------------------------------------------------
# Fleet Coordinator Root Agent & App Definition
# ---------------------------------------------------------------------------

router_fleet_coordinator = Agent(
    name="router_fleet_coordinator",
    model=fast_model_instance,
    description="Primary orchestrator for router fleet operations. Coordinates triage, telemetry analysis, SOP search, and remediation.",
    instruction="""
You are the Router Fleet Operations Coordinator.
You manage router fleet health, triage network anomalies, consult knowledge bases, and direct remediation actions.

Direct Execution & Delegation Workflow:
1. When asked to show, display, or render a router's status or card (e.g., "show the card for RTR-CAN-EAST-02"):
   - ALWAYS default to fetching the interactive A2UI card using `render_router_card(router_id)`.
   - Output ONLY the `<a2ui-json>` block verbatim with zero leading or trailing text.
   - ONLY fetch the visual PNG snapshot (`render_router_card_image`) if the user explicitly asks for an "image card", "PNG snapshot", or "picture card". In that case, return the response from `router_diagnostic_agent` confirming that the image card snapshot was rendered and saved as an artifact.
2. For diagnostic inquiry or troubleshooting requests, delegate telemetry gathering to `router_diagnostic_agent`.
3. Search standard operating procedures and knowledge bases via `router_knowledge_agent` to identify recommended recovery steps.
4. If remediation is required (BGP reset, reboot, LED update), delegate action execution to `router_remediation_agent`.
5. For non-UI text requests, synthesize all sub-agent results into a structured executive report detailing:
   - Target Router ID & Physical Location
   - Telemetry & Fault Findings
   - Knowledge Base Recovery Protocol
   - Actions Taken / Pending Human Confirmation
6. When a user action event or button click is received (e.g. `send_router_command` or power/reboot toggle):
   - Immediately execute `send_router_command(router_id=router_id, action=action)`.
   - Then call `render_router_card(router_id)` to fetch the new state.
   - Output ONLY the resulting `<a2ui-json>` payload verbatim starting with `<a2ui-json>` and ending with `</a2ui-json>`.
""",
    tools=[
        mcp_toolset,
    ],
    sub_agents=[
        router_diagnostic_agent,
        router_knowledge_agent,
        router_remediation_agent,
    ],
)

# Export root agent and App instance required by ADK runner & FastAPI
root_agent = router_fleet_coordinator
app = App(name="app", root_agent=root_agent)
