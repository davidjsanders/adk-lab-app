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

"""Safety Guardrail Plugin enforcing input/output policy security for ADK Agents."""

import logging
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins import BasePlugin
from google.genai import types

logger = logging.getLogger("router-ops-agent.plugins.guardrail")


class SafetyGuardrailPlugin(BasePlugin):
    """ADK Plugin enforcing runtime security guardrails on incoming LLM requests."""

    def __init__(self, name: str = "safety_guardrail_plugin") -> None:
        """Initializes the SafetyGuardrailPlugin instance.

        Args:
            name: Unique name identifier for the plugin.

        Returns:
            None.

        Raises:
            None.
        """
        super().__init__(name=name)

    async def before_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_request: LlmRequest,
    ) -> Optional[LlmResponse]:
        """Intercepts model requests before submission to evaluate safety guardrails.

        Args:
            callback_context: Context for the active agent turn.
            llm_request: Target LlmRequest payload sent to Gemini.

        Returns:
            LlmResponse to block execution if guardrail fails, or None to continue.

        Raises:
            None.
        """
        if llm_request.contents:
            for content in llm_request.contents:
                if not hasattr(content, "parts") or not content.parts:
                    continue
                for part in content.parts:
                    text = getattr(part, "text", "") or ""
                    if "rm -rf" in text or "drop database" in text.lower():
                        logger.warning("SafetyGuardrailPlugin: Blocked destructive command pattern in prompt.")
                        return LlmResponse(
                            content=types.Content(
                                role="model",
                                parts=[
                                    types.Part.from_text(
                                        text="[GUARDRAIL BLOCK] Request was blocked by SafetyGuardrailPlugin due to unauthorized command execution policy."
                                    )
                                ],
                            )
                        )
        return None
