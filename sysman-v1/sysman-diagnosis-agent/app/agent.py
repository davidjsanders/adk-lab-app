import logging
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.tools import VertexAiSearchTool
from app.classes.global_gemini import GlobalGemini
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sysman-diagnosis-agent.agent")

fast_model = GlobalGemini(model=settings.fast_model)

tools_list = []

# Instantiate Vertex AI Search tool if configurations exist
if settings.vertex_ai_search_project and settings.vertex_ai_search_data_store_id:
    data_store_path = (
        f"projects/{settings.vertex_ai_search_project}/"
        f"locations/{settings.vertex_ai_search_location}/"
        f"collections/default_collection/"
        f"dataStores/{settings.vertex_ai_search_data_store_id}"
    )
    logger.info(f"Diagnosis Agent initializing Vertex AI Search: {data_store_path}")
    try:
        search_tool = VertexAiSearchTool(data_store_id=data_store_path)
        tools_list.append(search_tool)
    except Exception as err:
        logger.error(f"Failed initializing VertexAiSearchTool: {err}")
else:
    logger.warning("Vertex AI Search environment variables are missing. Loading fallback mock runbook search tool.")

    def search_runbooks(query: str) -> dict:
        """Searches system runbooks and documentation for recovery and troubleshooting procedures.

        Args:
            query: The search query detailing the anomaly or error.

        Returns:
            Dictionary containing search results and instructions.
        """
        query_lower = query.lower()
        if "node_exporter" in query_lower or "process_down" in query_lower:
            return {
                "results": (
                    "RUNBOOK: Linux node_exporter offline.\n"
                    "1. Tactical action: Run START_NODE_EXPORTER command on the target system.\n"
                    "2. Verification: Verify status returns process_down=1.\n"
                    "3. Escalation: If it fails to start, verify logs for systemd config issues or reboot the VM."
                )
            }
        elif "jvm" in query_lower or "oom" in query_lower or "memory" in query_lower:
            return {
                "results": (
                    "RUNBOOK: Java Virtual Machine (JVM) OutOfMemory or Memory Creep.\n"
                    "1. Tactical action: Execute GC_CLEANUP command to force Garbage Collection and free Heap.\n"
                    "2. If memory continues to drift upwards, plan a system restart using RESTART_JIRA.\n"
                    "3. Note: A JVM restart will cause temporary application downtime."
                )
            }
        elif "websocket" in query_lower or "collaborative" in query_lower:
            return {
                "results": (
                    "RUNBOOK: Collaborative editor socket synchronization drop.\n"
                    "1. Tactical action: Send RECONNECT_WEBSOCKETS command to force web socket re-handshake.\n"
                    "2. If connectivity remains offline, execute a system REBOOT."
                )
            }
        elif "disk" in query_lower or "attachment" in query_lower:
            return {
                "results": (
                    "RUNBOOK: Application filesystem / attachments volume full.\n"
                    "1. Tactical action: Execute PURGE_ATTACHMENTS command to clean up cache, logs, and temp attachments.\n"
                    "2. Permanent action: Advise user to adjust storage size properties."
                )
            }
        elif "db_connections" in query_lower or "pool" in query_lower:
            return {
                "results": (
                    "RUNBOOK: Connection pool saturation.\n"
                    "1. Tactical action: Trigger EXPAND_DB_POOL command to scale JDBC limit to 100 connection leases.\n"
                    "2. If database capacity is exhausted, check logs for slow SQL statements."
                )
            }

        return {
            "results": (
                "GENERAL RUNBOOK: Inspect system status and logs to isolate errors.\n"
                "Use command actions (reboot, restarts, purges) matching the system type to restore health."
            )
        }

    tools_list.append(search_runbooks)


root_agent = Agent(
    name="sysman_diagnosis_agent",
    model=fast_model,
    description="Specialized troubleshooting agent that queries official runbooks and recovery documentation.",
    instruction="""
    You are the System Operations Diagnosis Specialist.
    Your objective is to find appropriate troubleshooting steps and runbooks for active system anomalies.

    Instructions:
    - Use the search tool to find solutions for the specific warning or anomaly query.
    - Read the search results carefully.
    - Extract and list the exact tactical steps required to remediate the warning (e.g. GC_CLEANUP for JVM leak, RECONNECT_WEBSOCKETS for Confluence websocket drop).
    - Report the recommended steps back to the Orchestrator.
    """,
    tools=tools_list
)

app = App(
    root_agent=root_agent,
    name="sysman_diagnosis_agent",
    plugins=[],
)
