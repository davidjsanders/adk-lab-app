import os
from urllib.parse import urlparse
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from app.agent import root_agent, app as adk_app

runner = Runner(
    app=adk_app,
    session_service=InMemorySessionService(),
    artifact_service=InMemoryArtifactService(),
    memory_service=InMemoryMemoryService()
)

# Dynamically resolve host, port, and protocol from APP_URL if available
app_url = os.getenv("APP_URL")
if app_url:
    parsed = urlparse(app_url)
    protocol = parsed.scheme or "http"
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if protocol == "https" else 80)
else:
    protocol = "http"
    host = "127.0.0.1"
    port = 8007

# Convert the ADK Agent to an A2A Starlette app
app = to_a2a(
    agent=root_agent,
    runner=runner,
    host=host,
    port=port,
    protocol=protocol
)

