"""Configuration settings for the Router Fleet Operations ADK Agent."""

import os
from dotenv import load_dotenv

# Load local environment variables from .env if present
load_dotenv(override=True)

# GCP and Vertex AI Configuration
GCP_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "agentspace-argolis-demo")
GCP_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
USE_VERTEXAI = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "True")

VERTEX_AI_SEARCH_DATASTORE_ID = os.getenv(
    "VERTEX_AI_SEARCH_DATASTORE_ID",
    f"projects/{GCP_PROJECT}/locations/global/collections/default_collection/dataStores/router-troubleshooting-kb"
)

# Fleet Infrastructure URLs
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://router-dashboard-cta6n7hkya-uc.a.run.app")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "https://router-mcp-server-63466983700.us-central1.run.app")

# Model Configuration
FAST_MODEL = os.getenv("FAST_MODEL", "gemini-3-flash-preview")
PRO_MODEL = os.getenv("PRO_MODEL", "gemini-3-pro-preview")
