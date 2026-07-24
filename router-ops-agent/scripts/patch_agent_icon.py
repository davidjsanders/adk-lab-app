#!/usr/bin/env python3
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

"""Utility script to patch registered agent icon URIs in Gemini Enterprise Discovery Engine."""

import sys
import google.auth
import google.auth.transport.requests
import requests

DEFAULT_ICON_URI = "https://fonts.gstatic.com/s/i/short-term/release/googlesymbols/router/default/48px.svg"


def patch_router_agent_icons(icon_uri: str = DEFAULT_ICON_URI) -> None:
    """Patches all Router Ops agent registrations in Discovery Engine to use the target icon.

    Args:
        icon_uri: Target icon URI string to apply.

    Returns:
        None.

    Raises:
        None.
    """
    credentials, project = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    token = credentials.token

    target_agents = [
        "projects/63466983700/locations/us/collections/default_collection/engines/agentspace-exemplar_1755693787640/assistants/default_assistant/agents/14510258352860043651",
    ]

    headers = {
        "Authorization": f"Bearer {token}",
        "x-goog-user-project": "63466983700",
        "Content-Type": "application/json",
    }
    payload = {"icon": {"uri": icon_uri}}

    print(f"Patching agent icons in Discovery Engine to: {icon_uri}")
    for agent_name in target_agents:
        url = f"https://us-discoveryengine.googleapis.com/v1alpha/{agent_name}?updateMask=icon"
        resp = requests.patch(url, headers=headers, json=payload)
        agent_id = agent_name.split("/")[-1]
        if resp.status_code == 200:
            print(f"  ✅ Agent '{agent_id}' updated successfully.")
        else:
            print(f"  ❌ Agent '{agent_id}' failed: {resp.status_code} - {resp.text}")


if __name__ == "__main__":
    target_uri = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ICON_URI
    patch_router_agent_icons(icon_uri=target_uri)


