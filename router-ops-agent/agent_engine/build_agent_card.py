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
import requests
from a2a import types as a2a_types
from a2a.types import AgentExtension
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card

logger = logging.getLogger(__name__)


def _get_cloud_run_url() -> str | None:
    """Dynamically constructs the Cloud Run service URL from GCP metadata server and env vars.

    Format: https://<service_name>-<project_number>.<location>.run.app
    """
    service_name = os.environ.get("K_SERVICE", "router-ops-agent")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"

    try:
        headers = {"Metadata-Flavor": "Google"}
        resp = requests.get(
            "http://metadata.google.internal/computeMetadata/v1/project/numeric-project-id",
            headers=headers,
            timeout=2,
        )
        if resp.status_code == 200:
            project_number = resp.text.strip()
            url = f"https://{service_name}-{project_number}.{location}.run.app"
            logger.info("Resolved Cloud Run URL from metadata server: %s", url)
            return url
        else:
            logger.warning("Metadata server returned status code %s", resp.status_code)
    except Exception as exc:
        logger.warning("Metadata server URL resolution exception: %s", exc)

    return None


def build_agent_card() -> a2a_types.AgentCard:
    """Builds and returns the A2A AgentCard for router-agent-v2 with A2UI capability."""
    skills = [
        {
            "id": "diagnostic_agent-telemetry_and_cards",
            "name": "diagnostic_telemetry",
            "description": "Inspects router hardware state, chassis LEDs, action logs, runs SNMP walks, and renders interactive A2UI dashboard cards via MCP server.",
            "examples": [
                "show the card for RTR-CAN-EAST-02",
                "check health and telemetry for router 1",
                "list router fleet",
            ],
            "tags": ["diagnostics", "a2ui", "telemetry", "snmp", "dashboard"]
        },
        {
            "id": "remediation_agent-hardware_and_bgp",
            "name": "remediation_actions",
            "description": "Executes high-reasoning BGP session resets, chassis reboots, fault tests, and LED maintenance overrides via MCP server.",
            "examples": [
                "reset BGP session on RTR-CAN-EAST-02",
                "reboot router 2",
                "set chassis LED to amber for maintenance"
            ],
            "tags": ["remediation", "bgp", "reboot", "led", "maintenance"]
        }
    ]

    card = create_agent_card(
        agent_name="router_fleet_coordinator",
        description="Router Fleet Operations Coordinator managing router fleet health, triage, diagnostics, interactive A2UI component rendering, and remediation.",
        skills=skills,
        streaming=True,
    )
    card.version = "0.2.0"

    # Add A2UI v0.8 capability extension for Gemini Enterprise and console card rendering
    if not hasattr(card, "capabilities") or card.capabilities is None:
        card.capabilities = a2a_types.AgentCapabilities(streaming=True)

    card.capabilities.extensions = [
        AgentExtension(
            uri="https://a2ui.org/a2a-extension/a2ui/v0.8",
            description="Ability to render A2UI",
            params={
                "supportedCatalogIds": [
                    "https://a2ui.org/specification/v0_8/standard_catalog_definition.json"
                ]
            },
        )
    ]

    cloud_run_url = _get_cloud_run_url()
    if cloud_run_url:
        card.url = f"{cloud_run_url}/a2a/app"
        logger.info("Successfully set card.url to: %s", card.url)
    else:
        logger.warning("cloud_run_url is None, card.url is: %s", getattr(card, "url", None))

    return card
