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

"""Patched GCP Skill Registry to fix HTTP 302 redirect handling."""

import httpx
from google.adk.integrations.skill_registry.gcp_skill_registry import GCPSkillRegistry


class PatchedGCPSkillRegistry(GCPSkillRegistry):
    """Subclass of GCPSkillRegistry that forces httpx to follow HTTP 302 redirects and increases timeouts."""

    def _create_httpx_client(self) -> httpx.AsyncClient:
        timeout = httpx.Timeout(30.0, connect=10.0)
        if self._ssl_context is not None:
            return httpx.AsyncClient(
                verify=self._ssl_context,
                follow_redirects=True,
                timeout=timeout,
            )
        return httpx.AsyncClient(follow_redirects=True, timeout=timeout)
