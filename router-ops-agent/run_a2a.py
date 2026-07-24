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

"""Dynamic A2A server execution script for router-agent-v2."""

import logging
import os
import uvicorn
from dotenv import load_dotenv

root_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(root_env)

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.artifacts.gcs_artifact_service import GcsArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.auth.credential_service.session_state_credential_service import SessionStateCredentialService

from app.agent import root_agent, app as adk_app
from app.config import settings
from a2a_agent.build_agent_card import build_agent_card
from a2a_agent.agent_executor_builder import agent_executor_builder

port = int(os.environ.get("PORT", "8000"))
host = os.environ.get("HOST", "0.0.0.0")

gcs_bucket = os.environ.get("GCS_ARTIFACT_BUCKET")
artifact_service = (
    GcsArtifactService(bucket_name=gcs_bucket)
    if gcs_bucket
    else InMemoryArtifactService()
)

runner = Runner(
    app=adk_app,
    session_service=InMemorySessionService(),
    artifact_service=artifact_service,
    memory_service=InMemoryMemoryService(),
    credential_service=SessionStateCredentialService(),
)

app = to_a2a(
    agent=root_agent,
    runner=runner,
    host=host,
    port=port,
    protocol="http",
    agent_card=build_agent_card(),
    agent_executor_factory=lambda **kwargs: agent_executor_builder(),
)

if __name__ == "__main__":
    uvicorn.run(app, host=host, port=port)
