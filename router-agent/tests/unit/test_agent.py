"""Unit tests for the Router Fleet Operations ADK Agent."""

from unittest.mock import MagicMock, patch

from app.agent import (
    root_agent,
    router_diagnostic_agent,
    router_knowledge_agent,
    router_remediation_agent,
)
from app.classes import TroubleshootingKnowledgeBase
from app.config import FAST_MODEL, PRO_MODEL
from app.helpers import GlobalGemini, build_proxy_headers
from app.models import (
    DiagnosticQueryResult,
    RemediationResult,
    RouterNodeMetadata,
)
from app.tools import (
    mcp_toolset,
    search_troubleshooting_knowledge_base,
)


def test_agent_hierarchy_structure_and_global_gemini_models():
    """Validates the multi-agent hierarchy topology and GlobalGemini model routing."""
    assert root_agent.name == "router_fleet_coordinator"
    assert isinstance(root_agent.model, GlobalGemini)
    assert root_agent.model.model == FAST_MODEL

    sub_agent_names = [sa.name for sa in root_agent.sub_agents]
    assert "router_diagnostic_agent" in sub_agent_names
    assert "router_knowledge_agent" in sub_agent_names
    assert "router_remediation_agent" in sub_agent_names

    # Check model split rules and GlobalGemini type wrapper
    assert isinstance(router_diagnostic_agent.model, GlobalGemini)
    assert router_diagnostic_agent.model.model == FAST_MODEL

    assert isinstance(router_knowledge_agent.model, GlobalGemini)
    assert router_knowledge_agent.model.model == FAST_MODEL

    assert isinstance(router_remediation_agent.model, GlobalGemini)
    assert router_remediation_agent.model.model == PRO_MODEL

    # Check that diagnostic and remediation agents utilize mcp_toolset
    assert mcp_toolset in router_diagnostic_agent.tools
    assert mcp_toolset in router_remediation_agent.tools


def test_pydantic_models_and_class_structure():
    """Validates app.models schemas and app.classes class definitions."""
    node = RouterNodeMetadata(
        id="RTR-TEST-01",
        name="Test Router",
        location="us-central1",
        purpose="Testing",
        url="http://127.0.0.1:8080",
    )
    assert node.id == "RTR-TEST-01"

    diag = DiagnosticQueryResult(status="success", router_id="RTR-TEST-01")
    assert diag.status == "success"

    remed = RemediationResult(
        status="success",
        action="reset_bgp",
        router_id="RTR-TEST-01",
        message="Done",
    )
    assert remed.action == "reset_bgp"

    kb_class = TroubleshootingKnowledgeBase(datastore_id="projects/test/dataStores/ds")
    search_res = kb_class.search("BGP down")
    assert search_res["status"] == "success"


def test_knowledge_base_search_grounding():
    """Tests SOP grounding query search for network anomalies."""
    result = search_troubleshooting_knowledge_base("BGP peering session down")
    assert result["status"] == "success"
    assert result["results_count"] > 0
    article = result["knowledge_articles"][0]
    assert "BGP" in article["issue"] or "Protocol" in article["issue"]


def test_impersonate_sa_auth_headers_via_python_sdk():
    """Validates that app.helpers.build_proxy_headers generates OIDC tokens natively via Python SDK IDTokenCredentials."""
    from app.helpers.auth import _OIDC_TOKEN_CACHE

    _OIDC_TOKEN_CACHE.clear()
    target_url = "https://router-mcp-server-63466983700.us-central1.run.app"
    mock_token = "eyJhbGciOiJSUzI1NiIsImt5aSI6IjEifQ.mocktoken"

    mock_target_creds = MagicMock()
    mock_target_creds.token = mock_token

    with (
        patch("google.auth.default", return_value=(MagicMock(), "test-proj")),
        patch(
            "app.helpers.auth.IDTokenCredentials",
            return_value=mock_target_creds,
        ) as mock_id_creds,
    ):
        headers = build_proxy_headers(target_url)
        assert "Authorization" in headers
        assert headers["Authorization"] == f"Bearer {mock_token}"
        assert headers["X-Serverless-Authorization"] == f"Bearer {mock_token}"

        mock_id_creds.assert_called_once()
        mock_target_creds.refresh.assert_called_once()


def test_auth_headers_forces_base_url_audience():
    """Validates that target audience scope is strictly the base URL origin without subpaths."""
    from app.helpers.auth import _OIDC_TOKEN_CACHE

    _OIDC_TOKEN_CACHE.clear()
    subpath_url = "https://router-mcp-server-63466983700.us-central1.run.app/mcp/sse?session_id=123"
    expected_audience = "https://router-mcp-server-63466983700.us-central1.run.app"

    mock_target_creds = MagicMock()
    mock_target_creds.token = "mock-token"

    with (
        patch("google.auth.default", return_value=(MagicMock(), "test-proj")),
        patch(
            "app.helpers.auth.IDTokenCredentials",
            return_value=mock_target_creds,
        ) as mock_id_creds,
    ):
        build_proxy_headers(subpath_url)
        mock_id_creds.assert_called_once()
        actual_audience = mock_id_creds.call_args[1].get("target_audience")
        assert actual_audience == expected_audience
