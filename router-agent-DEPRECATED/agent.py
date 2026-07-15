"""Router Fleet Operations ADK Agent definitions and Multi-Agent Orchestration.

Implements hierarchical multi-agent design pattern with strategic model routing:
- Root Fleet Coordinator (Flash): Orchestration & User Triage
- Diagnostic Specialist (Flash): Telemetry, Log Analysis & Anomaly Detection
- Knowledge Search Specialist (Flash): Vertex AI Search & SOP Retrieval
- Remediation Specialist (Pro): High-reasoning Remediation Planning & High-Stakes Action Dispatch

Includes EventsCompactionConfig for history compaction and session state persistence.
"""

import logging
from typing import Optional

from google.adk.agents import Agent
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.models import Gemini

from config import FAST_MODEL, PRO_MODEL, GCP_PROJECT, GCP_LOCATION
from tools import (
    ALL_TOOLS,
    fetch_router_hardware_logs,
    get_router_telemetry_status,
    inject_fault_tool,
    list_router_fleet_nodes,
    reboot_chassis_tool,
    reset_bgp_tool,
    run_router_snmp_walk,
    search_troubleshooting_knowledge_base,
    set_router_chassis_led,
)

logger = logging.getLogger("router-agent.agent")

# ---------------------------------------------------------------------------
# System Instructions & Constitutions
# ---------------------------------------------------------------------------

COORDINATOR_SYSTEM_INSTRUCTION = """
You are the Chief Coordinator for the Router Fleet Operations AI Suite.
Your primary role is to oversee router fleet health, triage incoming user requests, and orchestrate diagnostic, grounding, and remediation workflows across specialist agents.

Operational Principles:
1. When a user reports a problem (or asks for fleet inspection), invoke the Diagnostic Specialist Agent (`router_diagnostic_agent`) to gather telemetry, logs, and state across router nodes.
2. If anomalies (such as BGP state DOWN, abnormal LED indicators, or elevated log errors) are identified, route to the Knowledge Search Agent (`router_knowledge_agent`) to pull Standard Operating Procedures (SOPs) and troubleshooting guidelines.
3. For recovery and remediation tasks (e.g., clearing failure modes, resetting BGP sessions, rebooting router chassis), hand off to the Remediation Specialist Agent (`router_remediation_agent`).
4. Always provide clear, structured summaries of actions taken, current fleet health, and required human confirmation steps.
"""

DIAGNOSTIC_SPECIALIST_INSTRUCTION = """
You are the Router Fleet Diagnostic Specialist.
Your purpose is to inspect hardware chassis telemetry, query BGP protocol states, analyze operational logs, and perform SNMP MIB walks across router nodes to detect failures.

Diagnostic Protocol:
1. Always list active fleet nodes with `list_router_fleet_nodes` if the target router ID is unknown.
2. Fetch full operational state and LED statuses using `get_router_telemetry_status`.
3. If errors or link degradations are reported, retrieve historical hardware logs using `fetch_router_hardware_logs`.
4. If interface or protocol metrics need verification, run `run_router_snmp_walk`.
5. Clearly specify any detected failure conditions (e.g. "CRITICAL FAULT: Router RTR-CAN-EAST-01 BGP session is DOWN").
"""

KNOWLEDGE_SPECIALIST_INSTRUCTION = """
You are the Troubleshooting Knowledge Grounding Specialist.
Your role is to query Vertex AI Search and standard operational manuals to provide precise mitigation procedures for identified router anomalies.

Grounding Guidelines:
1. Use `search_troubleshooting_knowledge_base` to retrieve SOP guidelines for error symptoms (e.g. BGP peering loss, thermal degradation, dropped packets).
2. Summarize key recommended resolution steps clearly.
3. Highlight severity levels and prerequisites required before remediation.
"""

REMEDIATION_SPECIALIST_INSTRUCTION = """
You are the High-Reasoning Router Remediation Specialist.
You utilize advanced reasoning to synthesize diagnostic evidence, evaluate operational risk, and dispatch hardware recovery actions.

Remediation Guidelines:
1. Formulate a precise, safe remediation plan based on diagnostic findings and SOP guidelines.
2. For BGP protocol failure states, issue `reset_router_bgp_peering`.
3. For unrecoverable state locks or POST diagnostic needs, execute `reboot_router_chassis`.
4. When testing failure recovery, use `inject_router_bgp_fault_test`.
5. Adjust chassis indicator lights using `set_router_chassis_led` to reflect operational state.
6. NOTE: High-stakes tools (`reset_router_bgp_peering`, `reboot_router_chassis`, `inject_router_bgp_fault_test`) require explicit human confirmation before dispatch. Explain the rationale clearly.
"""

# ---------------------------------------------------------------------------
# Specialist Agents (Sub-Agents)
# ---------------------------------------------------------------------------

# 1. Diagnostic Specialist Agent (Flash)
diagnostic_agent = Agent(
    name="router_diagnostic_agent",
    model=FAST_MODEL,
    description="Inspects router fleet telemetry, BGP status, hardware logs, and SNMP metrics to identify anomalies.",
    instruction=DIAGNOSTIC_SPECIALIST_INSTRUCTION,
    tools=[
        list_router_fleet_nodes,
        get_router_telemetry_status,
        fetch_router_hardware_logs,
        run_router_snmp_walk,
    ],
)

# 2. Knowledge Search Agent (Flash)
knowledge_agent = Agent(
    name="router_knowledge_agent",
    model=FAST_MODEL,
    description="Queries Vertex AI Search and operational SOP manuals to retrieve troubleshooting procedures.",
    instruction=KNOWLEDGE_SPECIALIST_INSTRUCTION,
    tools=[
        search_troubleshooting_knowledge_base,
    ],
)

# 3. Remediation Specialist Agent (Pro - High Reasoning)
remediation_agent = Agent(
    name="router_remediation_agent",
    model=PRO_MODEL,
    description="Formulates recovery plans and dispatches high-stakes hardware commands with human confirmation.",
    instruction=REMEDIATION_SPECIALIST_INSTRUCTION,
    tools=[
        reset_bgp_tool,
        reboot_chassis_tool,
        inject_fault_tool,
        set_router_chassis_led,
    ],
)

# ---------------------------------------------------------------------------
# Root Coordinator Agent
# ---------------------------------------------------------------------------

root_agent = Agent(
    name="router_fleet_coordinator",
    model=FAST_MODEL,
    description="Root coordinator managing fleet diagnosis, knowledge search grounding, and remediation orchestration.",
    instruction=COORDINATOR_SYSTEM_INSTRUCTION,
    sub_agents=[
        diagnostic_agent,
        knowledge_agent,
        remediation_agent,
    ],
    tools=ALL_TOOLS,
)

# ---------------------------------------------------------------------------
# ADK App Instance with History Compaction
# ---------------------------------------------------------------------------

app = App(
    name="router_agent_app",
    root_agent=root_agent,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=15,  # Summarize history every 15 events to maintain context performance
        overlap_size=3,          # Keep last 3 events in sliding window for continuity
    ),
)
