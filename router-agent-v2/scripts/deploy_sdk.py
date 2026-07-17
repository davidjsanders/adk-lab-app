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

import sys
import os
import logging

print("Loading Vertex AI and ADK libraries...", flush=True)

# Add project root directory to path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from agent_engine.deployer import AgentEngineDeployer
from agent_engine.a2a_agent import get_a2a_agent
from agent_engine.helpers import (
    configure_paths,
    load_environment,
    setup_gcloud,
    refine_environment,
)

def deploy():
    """Orchestrates packaging and deploying the native A2aAgent to Vertex AI Agent Runtime."""
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )

    requirements_path = configure_paths()
    env_vars_to_forward = load_environment()
    project, location, staging_bucket = setup_gcloud()
    env = refine_environment(env_vars_to_forward)

    display_name = os.environ.get("DISPLAY_NAME", "router-agent-v2")
    agent_id = os.environ.get("AGENT_ID")
    service_account = os.environ.get("SERVICE_ACCOUNT")

    iam_only = "--iam-only" in sys.argv or "--iam_only" in sys.argv
    if iam_only:
        if not agent_id:
            raise ValueError("AGENT_ID must be configured in agentengine.env to run IAM-only configuration.")
        print(f"Configuring secure AGENT_IDENTITY IAM roles for agent ID: {agent_id}...")
        deployer = AgentEngineDeployer(
            project=project,
            location=location,
            staging_bucket=staging_bucket,
        )
        deployer.configure_iam_only(agent_id=agent_id)
        print("IAM role bindings successfully completed!")
        return

    print(f"Loading and initializing native A2aAgent: {display_name}...")
    a2a_agent = get_a2a_agent()

    deployer = AgentEngineDeployer(
        project=project,
        location=location,
        staging_bucket=staging_bucket,
    )

    deployer.deploy(
        agent=a2a_agent,
        display_name=display_name,
        requirements_path=requirements_path,
        agent_id=agent_id,
        env_vars=env,
        service_account=service_account,
    )

if __name__ == "__main__":
    deploy()
