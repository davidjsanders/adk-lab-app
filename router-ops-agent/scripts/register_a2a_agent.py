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

"""Registers or updates Agent definition in Gemini Enterprise Discovery Engine using provisionedReasoningEngine."""

import json
import os
import sys
import google.auth
import google.auth.transport.requests
import requests

# Ensure project root is in path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.append(project_dir)

DEFAULT_ICON_URI = "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/router/default/48px.svg"


def register_a2a_agent(agent_display_name: str = "Router V2") -> None:
    """Registers or updates an agent in Discovery Engine using provisionedReasoningEngine.

    Args:
        agent_display_name: Target display name in Gemini Enterprise UI.

    Returns:
        None.
    """
    credentials, project = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)

    # Load deployment metadata for engine ID
    metadata_path = os.path.join(project_dir, "deployment_metadata.json")
    reasoning_engine_resource = "projects/63466983700/locations/us-central1/reasoningEngines/4274515829967552512"
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            engine_path = meta.get("remote_agent_runtime_id", "")
            if engine_path:
                reasoning_engine_resource = engine_path

    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "x-goog-user-project": project,
        "Content-Type": "application/json",
    }

    parent = f"projects/{project}/locations/us/collections/default_collection/engines/agentspace-exemplar_1755693787640/assistants/default_assistant"

    # Find existing Agent by display name
    list_url = f"https://us-discoveryengine.googleapis.com/v1alpha/{parent}/agents"
    list_resp = requests.get(list_url, headers=headers)
    existing_agent_name = None

    if list_resp.status_code == 200:
        agents = list_resp.json().get("agents", [])
        for agent in agents:
            if agent.get("displayName") == agent_display_name:
                existing_agent_name = agent.get("name")
                break

    if existing_agent_name:
        # Delete existing agent to allow clean type registration
        print(f"Removing existing registration '{existing_agent_name}' for update...")
        requests.delete(f"https://us-discoveryengine.googleapis.com/v1alpha/{existing_agent_name}", headers=headers)

    # Create agent registration with provisionedReasoningEngine
    print(f"Creating agent registration '{agent_display_name}' in Discovery Engine...")
    create_payload = {
        "displayName": agent_display_name,
        "description": "Router Fleet Operations Coordinator managing router fleet health, triage, diagnostics, interactive A2UI component rendering, and remediation.",
        "icon": {
            "uri": DEFAULT_ICON_URI
        },
        "adkAgentDefinition": {
            "toolSettings": {},
            "provisionedReasoningEngine": {
                "reasoningEngine": reasoning_engine_resource
            }
        }
    }
    create_resp = requests.post(list_url, headers=headers, json=create_payload)
    if create_resp.status_code == 200:
        new_agent = create_resp.json()
        print(f"✅ Successfully registered '{agent_display_name}' in Discovery Engine: {new_agent.get('name')}")
    else:
        print(f"❌ Error registering agent in Discovery Engine: {create_resp.status_code} - {create_resp.text}")


if __name__ == "__main__":
    target_name = sys.argv[1] if len(sys.argv) > 1 else "Router V2"
    register_a2a_agent(agent_display_name=target_name)
