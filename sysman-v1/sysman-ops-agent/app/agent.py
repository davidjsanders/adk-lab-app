import logging
import os
from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.adk.apps import App
from app.classes.global_gemini import GlobalGemini
from app.config import settings
from app.helpers.auth import get_authenticated_client
from app.plugins.a2ui_plugin import A2UIPlugin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sysman-ops-agent.agent")

# Initialize models
fast_model = GlobalGemini(model=settings.fast_model)
pro_model = GlobalGemini(model=settings.pro_model)

# Shared A2UI Plugin instance
a2ui_plugin = A2UIPlugin()

# ---------------------------------------------------------------------------
# Resolve Detection Agent (A2A or Registry lookup)
# ---------------------------------------------------------------------------
detection_url = os.getenv("DETECTION_AGENT_URL")
if detection_url:
    if not detection_url.endswith(".json"):
        detection_url = f"{detection_url.rstrip('/')}{AGENT_CARD_WELL_KNOWN_PATH}"
    logger.info(f"Connecting to Remote Detection Agent via URL: {detection_url}")
    detection_agent = RemoteA2aAgent(
        name="detection_agent",
        description="Specialized monitoring and anomaly detection agent that reviews telemetry, metrics and alert trends.",
        agent_card=detection_url,
        httpx_client=get_authenticated_client(detection_url)
    )
else:
    try:
        from google.adk.integrations.agent_registry import AgentRegistry
        project_id = settings.google_cloud_project
        location = settings.google_cloud_location
        logger.info(f"Resolving detection_agent from Agent Registry ({project_id}/{location})...")
        registry = AgentRegistry(project_id=project_id, location=location)
        detection_agent = registry.get_remote_a2a_agent(
            agent_name=f"projects/{project_id}/locations/{location}/agents/sysman-detection-agent"
        )
    except Exception as err:
        logger.warning(f"Failed Agent Registry lookup for detection_agent: {err}. Falling back to local default.")
        fallback_url = f"http://127.0.0.1:8006{AGENT_CARD_WELL_KNOWN_PATH}"
        detection_agent = RemoteA2aAgent(
            name="detection_agent",
            description="Specialized monitoring and anomaly detection agent.",
            agent_card=fallback_url
        )

# ---------------------------------------------------------------------------
# Resolve Diagnosis Agent (A2A or Registry lookup)
# ---------------------------------------------------------------------------
diagnosis_url = os.getenv("DIAGNOSIS_AGENT_URL")
if diagnosis_url:
    if not diagnosis_url.endswith(".json"):
        diagnosis_url = f"{diagnosis_url.rstrip('/')}{AGENT_CARD_WELL_KNOWN_PATH}"
    logger.info(f"Connecting to Remote Diagnosis Agent via URL: {diagnosis_url}")
    diagnosis_agent = RemoteA2aAgent(
        name="diagnosis_agent",
        description="Specialized troubleshooting agent that queries official runbooks and recovery documentation.",
        agent_card=diagnosis_url,
        httpx_client=get_authenticated_client(diagnosis_url)
    )
else:
    try:
        from google.adk.integrations.agent_registry import AgentRegistry
        project_id = settings.google_cloud_project
        location = settings.google_cloud_location
        logger.info(f"Resolving diagnosis_agent from Agent Registry ({project_id}/{location})...")
        registry = AgentRegistry(project_id=project_id, location=location)
        diagnosis_agent = registry.get_remote_a2a_agent(
            agent_name=f"projects/{project_id}/locations/{location}/agents/sysman-diagnosis-agent"
        )
    except Exception as err:
        logger.warning(f"Failed Agent Registry lookup for diagnosis_agent: {err}. Falling back to local default.")
        fallback_url = f"http://127.0.0.1:8007{AGENT_CARD_WELL_KNOWN_PATH}"
        diagnosis_agent = RemoteA2aAgent(
            name="diagnosis_agent",
            description="Specialized troubleshooting agent.",
            agent_card=fallback_url
        )


root_agent = Agent(
    name="sysman_orchestrator",
    model=fast_model,
    description="Primary orchestrator for system management operations. Coordinates detection, diagnostics lookup, and remediation.",
    instruction="""
    You are the SysMan Operations Orchestrator (The Hub).
    Your goal is to coordinate system health audits, troubleshoot outages, and direct remediation.

    CRITICAL SAFEGUARD:
    - You have NO direct tools of your own to query hosts, list metrics, query runbooks, or run command actions.
    - You MUST delegate ALL actions to the appropriate sub-agent using `transfer_to_agent`. Do NOT attempt to resolve requests yourself.

    Delegation & Routing Workflow:
    1. When asked to audit health, check status, list systems, inspect resource usage, or render a status card/layout:
       - ALWAYS delegate the request to `detection_agent`. Do NOT invoke MCP tools yourself.
    2. When asked to look up a runbook, search documentation, or diagnose how to resolve a specific alarm/error:
       - ALWAYS delegate the request to `diagnosis_agent` (who will query Vertex AI Search / local documentation).
    3. If the user wants to apply a fix, remediate an issue (e.g. restart a service, reboot, run GC), or INJECT a fault/issue for demo testing:
       - ALWAYS delegate the action to `detection_agent` (who has direct command controls).

    Verbatim Relay Rule:
    - If any sub-agent returns a response containing `<a2ui-json>` and `</a2ui-json>`, you MUST relay that entire response (including any prepended warning messages and the A2UI block) to the user verbatim.
    - Do NOT strip or omit any warning messages prepended by the sub-agent.
    """,
    tools=[],
    sub_agents=[
        detection_agent,
        diagnosis_agent
    ]
)

app = App(
    root_agent=root_agent,
    name="app",
    plugins=[a2ui_plugin],
)
