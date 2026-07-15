# DESIGN_SPEC.md: Router Fleet Operations ADK Diagnostic Agent

## Overview

The **Router Fleet Operations ADK Agent** is an enterprise-grade AI system built with Google ADK (Agent Development Kit). It autonomously monitors, diagnoses, grounds, and remediates network hardware and peering issues across router fleets managed via the Router Fleet Operations Dashboard and Model Context Protocol (MCP) server.

The agent adheres strictly to the **AgentOps Code Review Matrix Rubrics**, featuring:
- **Comprehensive Tool Interfaces**: Typed Pydantic schemas, explicit docstrings, descriptive naming, and guided error handling.
- **Robust Context & Compaction**: Explicit system instructions, event history compaction (`EventsCompactionConfig`), and persistent session management.
- **Hierarchical Multi-Agent Architecture**: Strategic model routing using `gemini-3-flash-preview` for real-time telemetry gathering & search, and `gemini-3-pro-preview` for deep remediation planning.
- **Vertex AI Search Grounding**: Retrieval of standard operating procedures (SOPs), BGP troubleshooting guides, and chassis resolution steps from Vertex AI Search datastores.
- **Human-in-the-Loop Safeguards**: Mandatory confirmation steps (`require_confirmation=True`) before executing high-stakes chassis commands (reboots, session resets, fault injections).
- **Enterprise Deployability**: Ready for Agent Runtime deployment (`adk deploy agent_engine` / `agents-cli deploy agent_runtime`) and registration with Gemini Enterprise (`agents-cli publish gemini-enterprise`).

---

## Architecture & Multi-Agent Design Pattern

```
                             ┌───────────────────────────────────┐
                             │    Root Fleet Coordinator Agent   │
                             │     (gemini-3-flash-preview)      │
                             └─────────────────┬─────────────────┘
                                               │
               ┌───────────────────────────────┼───────────────────────────────┐
               ▼                               ▼                               ▼
 ┌───────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────┐
 │   Diagnostic Specialist   │   │     Grounding Specialist  │   │   Remediation Specialist  │
 │ (gemini-3-flash-preview)  │   │ (gemini-3-flash-preview)  │   │   (gemini-3-pro-preview)  │
 │ - MCP Telemetry Query     │   │ - Vertex AI Search        │   │ - BGP Reset / Reboot      │
 │ - Hardware Logs & SNMP    │   │ - SOP & Guide Retrieval   │   │ - Human Confirmation Hook │
 └───────────────────────────┘   └───────────────────────────┘   └───────────────────────────┘
```

1. **Root Fleet Coordinator Agent** (`router_fleet_coordinator`):
   - Model: `gemini-3-flash-preview`
   - Role: System entrance, intent routing, state management, and user interaction orchestration.
2. **Diagnostic Specialist Agent** (`router_diagnostic_agent`):
   - Model: `gemini-3-flash-preview`
   - Role: Interacts with the Router MCP server (`router-mcp-server`) to inspect router list, node status, BGP state, LED indicators, hardware logs, and SNMP MIB trees. Identifies root cause anomalies.
3. **Grounding Specialist Agent** (`router_knowledge_agent`):
   - Model: `gemini-3-flash-preview`
   - Role: Queries Vertex AI Search (and fallback local knowledge base) for diagnostic grounding, SOP step retrieval, and failure mitigation guidelines.
4. **Remediation Specialist Agent** (`router_remediation_agent`):
   - Model: `gemini-3-pro-preview`
   - Role: Constructs step-by-step remediation plans. Dispatches high-stakes hardware commands (session resets, POST diagnostic reboots, LED adjustments) with mandatory human confirmation hooks.

---

## Tool Interface Specifications

Every tool follows standard ADK tool requirements:
1. Complete docstrings (Summary, `Args:`, `Returns:`, `Raises:`).
2. JSON-serializable structured responses.
3. Guided error handling with `"status": "error"`, `"error": ...`, and `"recovery_instruction"`.

### MCP Server Integration Tools
- `list_router_fleet_nodes`: Queries all registered router nodes in the fleet.
- `get_router_telemetry_status`: Returns state, LED indicators, BGP status, uptime, and hardware health for a specific node.
- `fetch_router_hardware_logs`: Fetches operational logs filtered by time window and severity.
- `run_router_snmp_walk`: Queries SNMP OID tree for hardware telemetry.

### Remediation & Control Tools (With Confirmation Hooks)
- `reset_router_bgp_peering`: Restores BGP peering session state. (`require_confirmation=True`)
- `reboot_router_chassis`: Triggers POST diagnostic system reboot. (`require_confirmation=True`)
- `inject_router_bgp_fault_test`: Injects BGP failure state for fault testing. (`require_confirmation=True`)
- `set_router_chassis_led`: Adjusts chassis LED indicators.

### Grounding & Search Tools
- `search_troubleshooting_knowledge_base`: Queries Vertex AI Search datastore / SOP manuals for network fault troubleshooting.

---

## Deployment & Enterprise Publishing

- **Deployment Target**: Agent Runtime (Vertex AI Reasoning Engine / Agent Engine).
- **Metadata**: Generated `deployment_metadata.json` enabling programmatic publishing.
- **Publishing command**: `agents-cli publish gemini-enterprise --registration-type adk`
