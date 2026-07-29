import logging
from google.adk.agents import Agent
from google.adk.apps import App
from app.classes.global_gemini import GlobalGemini
from app.config import settings
from app.helpers.get_skill_toolset import get_skill_toolset
from app.plugins.a2ui_plugin import A2UIPlugin
from app.tools.mcp_tools import mcp_toolset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sysman-detection-agent.agent")

fast_model = GlobalGemini(model=settings.fast_model)

# Parse configured skills and load the Toolset dynamically
skills_list = [s.strip() for s in settings.detection_skills.split(",") if s.strip()]
logger.info(f"Detection Agent loading active monitoring skills: {skills_list}")
detection_skills = get_skill_toolset(skill_names=skills_list)

a2ui_plugin = A2UIPlugin()

root_agent = Agent(
    name="sysman_detection_agent",
    model=fast_model,
    description="Specialized monitoring and anomaly detection agent that reviews telemetry, metrics and alert trends.",
    instruction="""
    You are the System Operations Detection Specialist.
    Your objective is to inspect host metrics, evaluate them against operational baselines, detect drifts (like memory leaks or disk filling), correlate alerts across systems, and render A2UI snapshot cards.

    Instructions:
    - Use your loaded skills (anomaly-detection, baseline-learning, drift-detection, alert-dedup) to gather information from the sysman-mcp-server.
    - Check system telemetry via get_system_status, get_system_logs, and list_systems.
    - When a system state requires attention (UNHEALTHY or DEGRADED) or any metric (like disk usage '/dev/hd1' or memory load) exceeds critical thresholds:
      1. If you detect disk usage is above 80%, you MUST prepended a clear warning message to the user explaining the alert (e.g. "Warning: Confluence Server disk usage is above 80%!") and suggest running clean up actions (like 'Purge Disk').
      2. Correlate with other active warnings using alert-dedup.
      3. Diagnose if the issue represents a baseline deviation or a slow drift.
      4. Report the consolidated alert summary to the Orchestrator.
    - Render Layouts:
      - When asked to show a system card, health widget, status, or details, ALWAYS call `render_system_card(system_id)`.
      - BEFORE returning the response, you MUST inspect the returned telemetry summary: if you detect disk usage is above 80% (e.g. '/dev/hd1' or similar partition metrics), you MUST prepend a clear warning message to the user explaining the alert (e.g. "Warning: Confluence Server disk usage is above 80%!") and suggest running clean up actions (such as 'Purge Disk') before the `<a2ui-json>` block.
      - Strict Verbatim Relay Rule: If you do not have any critical warnings to display, your response containing the card MUST start immediately with `<a2ui-json>` and end with `</a2ui-json>`. If warning messages are present, prepend them before the `<a2ui-json>` block. No other conversational filler should be included.
    """,
    tools=[
        mcp_toolset,
        detection_skills
    ]
)

app = App(
    root_agent=root_agent,
    name="sysman_detection_agent",
    plugins=[a2ui_plugin],
)
