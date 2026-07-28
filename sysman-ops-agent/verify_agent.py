import os
import subprocess
import time
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


def test_agent_end_to_end():
    # 1. Start sysman-emulator in background on port 8085
    print("Starting sysman-emulator on port 8085...")
    emulator_dir = os.path.abspath("../sysman-emulator")
    emulator_proc = subprocess.Popen(
        [".venv/bin/python", "app.py"],
        cwd=emulator_dir,
        env={"PORT": "8085", "CONTROL_PASSWORD": "TestPass123!"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # 2. Start sysman-mcp-server in background on port 8005
    print("Starting sysman-mcp-server on port 8005...")
    mcp_dir = os.path.abspath("../sysman-mcp-server")
    mcp_proc = subprocess.Popen(
        [".venv/bin/python", "server.py"],
        cwd=mcp_dir,
        env={
            "PORT": "8005",
            "EMULATOR_URL": "http://127.0.0.1:8085",
            "CONTROL_PASSWORD": "TestPass123!",
            "CONTROL_HEADER": "X-Control-Password"
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for MCP server to start up
    time.sleep(2.0)

    # 3. Start sysman-detection-agent A2A server in background on port 8006
    print("Starting remote sysman-detection-agent A2A service on port 8006...")
    detection_agent_dir = os.path.abspath("../sysman-detection-agent")
    detection_proc = subprocess.Popen(
        [".venv/bin/python", "-m", "uvicorn", "app.fast_api_app:app", "--port", "8006"],
        cwd=detection_agent_dir,
        env={
            "MCP_SERVER_URL": "http://127.0.0.1:8005",
            "FAST_MODEL": "gemini-3-flash-preview",
            "PRO_MODEL": "gemini-3.1-pro-preview",
            "GOOGLE_GENAI_USE_VERTEXAI": "True",
            "GOOGLE_CLOUD_PROJECT": "agentspace-argolis-demo",
            "GOOGLE_CLOUD_LOCATION": "us-central1"
        },
        stdout=subprocess.PIPE,
        stderr=None
    )

    # 4. Start sysman-diagnosis-agent A2A server in background on port 8007
    print("Starting remote sysman-diagnosis-agent A2A service on port 8007...")
    diagnosis_agent_dir = os.path.abspath("../sysman-diagnosis-agent")
    diagnosis_proc = subprocess.Popen(
        [".venv/bin/python", "-m", "uvicorn", "app.fast_api_app:app", "--port", "8007"],
        cwd=diagnosis_agent_dir,
        env={
            "FAST_MODEL": "gemini-3-flash-preview",
            "PRO_MODEL": "gemini-3.1-pro-preview",
            "GOOGLE_GENAI_USE_VERTEXAI": "True",
            "GOOGLE_CLOUD_PROJECT": "agentspace-argolis-demo",
            "GOOGLE_CLOUD_LOCATION": "us-central1"
        },
        stdout=subprocess.PIPE,
        stderr=None
    )

    # Wait for all remote services to warm up
    time.sleep(5.0)

    try:
        # Override environment variables for the Orchestrator App runtime
        os.environ["MCP_SERVER_URL"] = "http://127.0.0.1:8005"
        os.environ["DETECTION_AGENT_URL"] = "http://127.0.0.1:8006"
        os.environ["DIAGNOSIS_AGENT_URL"] = "http://127.0.0.1:8007"
        os.environ["FAST_MODEL"] = "gemini-3-flash-preview"
        os.environ["PRO_MODEL"] = "gemini-3.1-pro-preview"
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

        # Now import the app (forces Settings to reload from modified os.environ)
        from app.agent import app

        print("Initializing ADK Runner and Session Service...")
        session_service = InMemorySessionService()
        session = session_service.create_session_sync(user_id="test_user", app_name="sysman-ops-agent")

        runner = Runner(app=app, session_service=session_service)

        print("Sending message: 'Audit the health of linux-server-01. Show the card.'")
        user_message = types.Content(
            role="user",
            parts=[types.Part.from_text(text="Audit the health of linux-server-01. Show the card.")]
        )

        # Run synchronous turn
        events = list(
            runner.run(
                new_message=user_message,
                user_id="test_user",
                session_id=session.id
            )
        )

        print("\n--- Agent Execution Output Events ---")
        card_found = False
        for ev in events:
            # Look at output event content
            text_content = ""
            if ev.content and ev.content.parts:
                for part in ev.content.parts:
                    if part.text:
                        text_content += part.text
            
            print(f"[{ev.author}]: {text_content}")
            if "<a2ui-json>" in text_content:
                card_found = True

        print("---------------------------------------")
        print("Card rendered by A2UI Plugin:", card_found)
        assert card_found, "Validation Failed: Agent response did not render the A2UI card markup."
        print("Agent End-to-End Local Audit Test Passed!")

    finally:
        print("Stopping processes...")
        diagnosis_proc.terminate()
        diagnosis_proc.wait()
        detection_proc.terminate()
        detection_proc.wait()
        mcp_proc.terminate()
        mcp_proc.wait()
        emulator_proc.terminate()
        emulator_proc.wait()


if __name__ == "__main__":
    test_agent_end_to_end()
