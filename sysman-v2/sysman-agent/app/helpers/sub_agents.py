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

"""Helper function for resolving sub-agents from registry or fallback URLs using typed specifications."""

import logging
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.adk.integrations.agent_registry import AgentRegistry
from app.config import settings
from app.helpers.auth import get_authenticated_client
from app.models.sub_agents import AgentSpec, DiscoveredAgent

logger = logging.getLogger("sysman-agent.helpers.sub_agents")


def resolve_sub_agents(specs: list[AgentSpec]) -> list[DiscoveredAgent]:
    """Resolves a variable list of sub-agents from Agent Registry or fallback URLs.

    Args:
        specs: List of typed AgentSpec definitions.

    Returns:
        A list of resolved DiscoveredAgent instances.
    """
    project_id = settings.google_cloud_project
    location = settings.google_cloud_location
    suffix = settings.agent_registry_suffix

    discovered: list[DiscoveredAgent] = []

    # Try resolving from Agent Registry
    try:
        logger.info(f"Connecting to Agent Registry ({project_id}/{location}) for sub-agents (suffix: {suffix})...")
        registry = AgentRegistry(project_id=project_id, location=location)
        for spec in specs:
            agent_name = f"projects/{project_id}/locations/{location}/services/{spec.registry_id}-{suffix}"
            logger.info(f"Resolving {spec.name} from registry: {agent_name}")
            resolved_agent = registry.get_remote_a2a_agent(agent_name=agent_name)
            discovered.append(DiscoveredAgent(key=spec.key, agent=resolved_agent))
        return discovered
    except Exception as err:
        logger.warning(f"Failed Agent Registry lookup for sub-agents: {err}. Falling back to static URL configuration.")

    # Fall back to static URL configuration
    discovered.clear()
    for spec in specs:
        url = spec.static_url
        if not url.endswith(".json"):
            url = f"{url.rstrip('/')}{AGENT_CARD_WELL_KNOWN_PATH}"
        logger.info(f"Connecting to fallback Remote Agent '{spec.name}' via URL: {url}")
        resolved_agent = RemoteA2aAgent(
            name=spec.name,
            description=spec.description,
            agent_card=url,
            httpx_client=get_authenticated_client(url),
        )
        discovered.append(DiscoveredAgent(key=spec.key, agent=resolved_agent))

    return discovered
