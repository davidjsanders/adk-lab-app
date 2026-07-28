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

# Convert the ADK Agent to an A2A Starlette app on port 8006
app = to_a2a(
    agent=root_agent,
    runner=runner,
    host="127.0.0.1",
    port=8006
)
