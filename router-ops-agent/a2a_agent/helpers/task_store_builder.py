
import logging
import os

import vertexai
from a2a.contrib.tasks.vertex_task_store import VertexTaskStore
from a2a.server.tasks import InMemoryTaskStore

# from google.adk.a2a.server.tasks import InMemoryTaskStore

logger = logging.getLogger(__name__)


def task_store_builder():
    ae_id = os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID")
    if ae_id and ae_id != "test-agent-engine":

        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION")

        # Initialize Vertex Client
        client = vertexai.Client(project=project, location=location)

        agent_engine_resource_id = f"projects/{project}/locations/{location}/reasoningEngines/{ae_id}"
        logger.info(f"Using VertexTaskStore for resource: {agent_engine_resource_id}")
        return VertexTaskStore(client=client, agent_engine_resource_id=agent_engine_resource_id)
    else:
        logger.info("Using local InMemoryTaskStore")
        return InMemoryTaskStore()
