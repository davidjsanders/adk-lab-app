# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import warnings
import google.adk

from google.adk.artifacts import InMemoryArtifactService, GcsArtifactService
from google.adk.auth.credential_service.session_state_credential_service import SessionStateCredentialService
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from app.agent import app as adk_app
from app.config import settings
from .session_service import SessionService

logger = logging.getLogger(__name__)

async def create_runner() -> Runner:
    """Creates an ADK runner configured for Agent Runtime or local execution."""
    _setup_logging()
    logger.info(f"=== Initializing Router Agent Runner [ADK Version: {google.adk.__version__}] ===")

    gcs_bucket = os.environ.get("GCS_ARTIFACT_BUCKET")
    artifact_service = (
        GcsArtifactService(bucket_name=gcs_bucket)
        if gcs_bucket
        else InMemoryArtifactService()
    )

    ae_id = os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID")
    if ae_id and ae_id != "test-agent-engine":
        project_val = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID") or settings.google_cloud_project
        location_val = os.environ.get("GOOGLE_CLOUD_LOCATION") or os.environ.get("REGION") or settings.google_cloud_location
        logger.info(f"Using Vertex AI Session Service for Agent Engine ID: {ae_id} (Project: {project_val}, Location: {location_val})")
        session_service = SessionService(
            project=project_val,
            location=location_val,
            agent_engine_id=ae_id,
        )
    else:
        logger.info("Using local InMemorySessionService")
        session_service = InMemorySessionService()

    return Runner(
        app=adk_app,
        session_service=session_service,
        artifact_service=artifact_service,
        memory_service=InMemoryMemoryService(),
        credential_service=SessionStateCredentialService(),
    )

def _setup_logging():
    warnings.filterwarnings('ignore', message=r'.*EXPERIMENTAL.*')
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(module)s.%(funcName)s: %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(log_level)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    root_logger.addHandler(handler)

    logging.getLogger("router-agent").setLevel(log_level)
    logging.getLogger("google_adk").setLevel(log_level)
