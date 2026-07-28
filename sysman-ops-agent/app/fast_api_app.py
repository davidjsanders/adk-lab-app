import os
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Initialize standard ADK FastAPI application
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    otel_to_cloud=False,
)

app.title = "sysman-ops-agent"
app.description = "API endpoint for interacting with the SysMan Operations ADK Agent"
