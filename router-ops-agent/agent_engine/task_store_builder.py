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
import vertexai
from a2a.contrib.tasks.vertex_task_store import VertexTaskStore
from a2a.server.tasks import InMemoryTaskStore
from app.config import settings

logger = logging.getLogger(__name__)

def task_store_builder():
    """Returns a task store builder for the application."""
    logger.info("Building task store")
    ae_id = os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID")
    if ae_id and ae_id != "test-agent-engine":
        project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID") or settings.google_cloud_project
        location = os.environ.get("GOOGLE_CLOUD_LOCATION") or os.environ.get("REGION") or settings.google_cloud_location
        client = vertexai.Client(project=project, location=location)

        agent_engine_resource_id = (
            f"projects/{project}/"
            f"locations/{location}/"
            f"reasoningEngines/{ae_id}"
        )
        logger.info(
            "Using VertexTaskStore for resource: %s",
            agent_engine_resource_id,
        )
        return VertexTaskStore(
            client=client,
            agent_engine_resource_id=agent_engine_resource_id
        )
    else:
        logger.info("Using local InMemoryTaskStore")
        return InMemoryTaskStore()
