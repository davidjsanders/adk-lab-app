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
import sys

logger = logging.getLogger(__name__)

# Reserved environment variable names that Reasoning Engine automatically sets and rejects in deployment_spec.env
RESERVED_ENV_KEYS = {
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_CLOUD_LOCATION",
    "GOOGLE_CLOUD_REGION",
    "PROJECT_ID",
    "REGION",
    "AGENT_ID",
}

def configure_paths() -> str:
    """Appends necessary project paths to sys.path and resolves requirements file path."""
    agent_engine_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(agent_engine_dir)

    if project_dir not in sys.path:
        sys.path.append(project_dir)

    requirements_path = os.path.join(project_dir, "requirements.txt")
    logger.info("Resolved requirements path: %s", requirements_path)
    return requirements_path

def load_environment() -> list[str]:
    """Loads settings from scripts/agentengine.env or project .env into os.environ."""
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_dir = os.path.join(project_dir, "scripts")
    env_file = os.path.join(script_dir, "agentengine.env")
    env_vars_to_forward = []

    if not os.path.exists(env_file):
        env_file = os.path.join(project_dir, ".env")

    if os.path.exists(env_file):
        logger.info("Loading deployment environment from: %s", env_file)
        with open(env_file) as f:
            for line in f:
                line_str = line.strip()
                if line_str and not line_str.startswith("#"):
                    try:
                        key, value = line_str.split("=", 1)
                        key = key.strip()
                        os.environ[key] = value.strip('"').strip("'")
                        env_vars_to_forward.append(key)
                    except ValueError:
                        pass
    else:
        logger.warning("No environment configuration file found.")

    return env_vars_to_forward

def setup_gcloud() -> tuple[str, str, str]:
    """Retrieves and validates required Google Cloud configuration parameters."""
    project = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID", "agentspace-argolis-demo")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION") or os.environ.get("REGION", "us-central1")
    staging_bucket = os.environ.get("GOOGLE_CLOUD_STAGING_BUCKET", "ae-staging-bucket")

    os.environ["GOOGLE_CLOUD_PROJECT"] = project
    os.environ["GOOGLE_CLOUD_LOCATION"] = location
    os.environ["GOOGLE_CLOUD_STAGING_BUCKET"] = staging_bucket

    logger.info("GCP Config: Project=%s, Location=%s, StagingBucket=%s", project, location, staging_bucket)
    return project, location, staging_bucket

def refine_environment(env_vars_to_forward: list[str]) -> dict[str, str]:
    """Assembles environment variables dictionary to forward to the remote reasoning engine container."""
    env = {}
    for key in env_vars_to_forward:
        if key in os.environ and os.environ[key] != "":
            if key in RESERVED_ENV_KEYS:
                continue
            env[key] = os.environ[key]

    # Explicitly ensure MCP_SERVER_URL, DASHBOARD_URL, and model configs are forwarded
    critical_keys = ["MCP_SERVER_URL", "DASHBOARD_URL", "FAST_MODEL", "PRO_MODEL", "LOG_LEVEL", "VERSION", "GCS_ARTIFACT_BUCKET"]
    for critical_key in critical_keys:
        if critical_key in os.environ and critical_key not in env and critical_key not in RESERVED_ENV_KEYS:
            env[critical_key] = os.environ[critical_key]

    if "LOG_LEVEL" not in env:
        env["LOG_LEVEL"] = "INFO"

    logger.info("Refined environment keys to forward: %s", list(env.keys()))
    return env
