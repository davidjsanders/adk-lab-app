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

"""Deployment entrypoint script using Vertex AI GenAI SDK for Agent Runtime (A2A)."""

import logging
import os
import sys

# Ensure project root is in path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.append(project_dir)

import google.protobuf.json_format as json_format
from google.protobuf.struct_pb2 import Struct
from a2a.types import AgentCard

# Patch json_format helpers to convert Pydantic AgentCard to Protobuf Struct during Vertex SDK deployment
_original_message_to_json = json_format.MessageToJson
_original_message_to_dict = json_format.MessageToDict

def _patched_message_to_json(message, *args, **kwargs):
    if isinstance(message, AgentCard):
        s = Struct()
        s.update(message.model_dump(mode="json"))
        return _original_message_to_json(s, *args, **kwargs)
    return _original_message_to_json(message, *args, **kwargs)

def _patched_message_to_dict(message, *args, **kwargs):
    if isinstance(message, AgentCard):
        s = Struct()
        s.update(message.model_dump(mode="json"))
        return _original_message_to_dict(s, *args, **kwargs)
    return _original_message_to_dict(message, *args, **kwargs)

json_format.MessageToJson = _patched_message_to_json
json_format.MessageToDict = _patched_message_to_dict

from a2a_agent.a2a_agent import get_a2a_agent
from a2a_agent.deployer import AgentEngineDeployer
from a2a_agent.helpers import (
    configure_paths,
    load_environment,
    refine_environment,
    setup_gcloud,
)


def deploy() -> None:
    """Deploys native A2aAgent to Vertex AI Agent Runtime."""
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )

    requirements_path = configure_paths()
    env_vars_to_forward = load_environment()
    project, location, staging_bucket = setup_gcloud()
    env = refine_environment(env_vars_to_forward)

    display_name = os.environ.get("DISPLAY_NAME", "router-ops-agent")
    agent_id = os.environ.get("AGENT_ID")
    service_account = os.environ.get("SERVICE_ACCOUNT") or f"router-ops-agent-sa@{project}.iam.gserviceaccount.com"

    print(f"Loading and initializing local A2aAgent for: {display_name}...")
    a2a_agent = get_a2a_agent()

    deployer = AgentEngineDeployer(
        project=project,
        location=location,
        staging_bucket=staging_bucket,
    )

    resource_name = deployer.deploy(
        agent=a2a_agent,
        display_name=display_name,
        requirements_path=requirements_path,
        agent_id=agent_id,
        env_vars=env,
        service_account=service_account,
    )
    print(f"Deployment complete! Resource: {resource_name}")


if __name__ == "__main__":
    deploy()
