"""Unit tests for Router Fleet Operations ADK Agent tools and multi-agent setup."""

import pytest
from agent import app, root_agent, diagnostic_agent, knowledge_agent, remediation_agent
from tools import (
    list_router_fleet_nodes,
    get_router_telemetry_status,
    fetch_router_hardware_logs,
    run_router_snmp_walk,
    search_troubleshooting_knowledge_base,
    reset_router_bgp_peering,
    reboot_router_chassis,
    inject_router_bgp_fault_test,
    set_router_chassis_led,
)


def test_agent_structure_and_subagents():
    """Verify multi-agent hierarchy and strategic model choices."""
    assert root_agent.name == "router_fleet_coordinator"
    assert len(root_agent.sub_agents) == 3
    
    # Verify sub-agent names
    sub_names = [sa.name for sa in root_agent.sub_agents]
    assert "router_diagnostic_agent" in sub_names
    assert "router_knowledge_agent" in sub_names
    assert "router_remediation_agent" in sub_names

    # Strategic model routing verification
    assert root_agent.model == "gemini-3-flash-preview"
    assert diagnostic_agent.model == "gemini-3-flash-preview"
    assert knowledge_agent.model == "gemini-3-flash-preview"
    assert remediation_agent.model == "gemini-3-pro-preview"  # High-reasoning model for remediation


def test_knowledge_search_grounding():
    """Test troubleshooting knowledge base search tool."""
    res = search_troubleshooting_knowledge_base("BGP peering state down error")
    assert res["status"] == "success"
    assert res["results_count"] > 0
    assert "BGP" in res["knowledge_articles"][0]["issue"]
    assert len(res["knowledge_articles"][0]["recommended_steps"]) > 0


def test_guided_error_handling_when_dashboard_unreachable():
    """Verify tool returns structured error payload with LLM recovery guidance instead of crashing."""
    res = get_router_telemetry_status("INVALID-ROUTER-999")
    assert res["status"] == "error"
    assert "error" in res
    assert "recovery_instruction" in res
    assert "list_router_fleet_nodes" in res["recovery_instruction"] or "Verify" in res["recovery_instruction"]


def test_app_events_compaction_configuration():
    """Verify App events compaction config is active for long turn conversations."""
    assert app.name == "router_agent_app"
    assert app.events_compaction_config is not None
    assert app.events_compaction_config.compaction_interval == 15
    assert app.events_compaction_config.overlap_size == 3
