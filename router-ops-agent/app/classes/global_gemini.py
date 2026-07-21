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

"""Global Gemini model class override for ADK Agents.

Forces location='global' on the GenAI client to resolve model routing when
GOOGLE_CLOUD_LOCATION is set to a specific regional location (e.g. us-central1).
"""

import logging
import os
from functools import cached_property

from google.adk.models import Gemini
from google.genai import Client
from google.genai import types as genai_types

logger = logging.getLogger("router-ops-agent.classes.global_gemini")


class GlobalGemini(Gemini):
    """Gemini model subclass enforcing global location endpoint routing."""

    @staticmethod
    def is_vertex(model: str) -> bool:
        """Determines if the model uses Vertex AI.

        Args:
            model: Model name or resource string.

        Returns:
            Boolean indicating whether Vertex AI is enabled.
        """
        return (
            model.startswith("projects/")
            or os.getenv("GOOGLE_GENAI_USE_VERTEXAI") == "True"
        )

    @cached_property
    def api_client(self) -> Client:
        """Creates a Google GenAI API client configured with location='global'.

        Returns:
            Configured GenAI Client instance.
        """
        logger.debug("GlobalGemini api_client initialized for model: %s", self.model)
        base_url, api_version = self._base_url_and_api_version

        kwargs_for_http_options = {
            "headers": self._tracking_headers(),
            "retry_options": self.retry_options,
            "base_url": base_url,
        }

        if api_version:
            kwargs_for_http_options["api_version"] = api_version

        kwargs = {
            "http_options": genai_types.HttpOptions(**kwargs_for_http_options),
            "location": "global",
        }

        if self.is_vertex(self.model):
            kwargs["vertexai"] = True

        return Client(**kwargs)
