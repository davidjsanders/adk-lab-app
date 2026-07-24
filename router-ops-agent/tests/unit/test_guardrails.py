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

"""Unit tests for SafetyGuardrailPlugin and human confirmation callbacks."""

from types import SimpleNamespace
import pytest
from google.adk.models.llm_request import LlmRequest
from google.genai import types

from app.plugins.guardrail_plugin import SafetyGuardrailPlugin
from app.subagents.remediation_agent import require_human_confirmation


@pytest.mark.asyncio
async def test_safety_guardrail_plugin_blocks_destructive_commands():
    plugin = SafetyGuardrailPlugin()

    # Normal prompt passes through
    safe_request = LlmRequest(
        contents=[types.Content(role="user", parts=[types.Part.from_text(text="Show router status")])]
    )
    res = await plugin.before_model_callback(callback_context=None, llm_request=safe_request)
    assert res is None

    # Destructive prompt is blocked
    destructive_request = LlmRequest(
        contents=[types.Content(role="user", parts=[types.Part.from_text(text="Please run rm -rf /")])]
    )
    res_blocked = await plugin.before_model_callback(callback_context=None, llm_request=destructive_request)
    assert res_blocked is not None
    assert "[GUARDRAIL BLOCK]" in res_blocked.content.parts[0].text


@pytest.mark.asyncio
async def test_human_confirmation_callback():
    tool = SimpleNamespace(name="reset_bgp_session")

    class DummyContext:
        def __init__(self, confirmed=False):
            self.state = {"human_confirmed": confirmed}

    # Unconfirmed action is intercepted
    unconfirmed_ctx = DummyContext(confirmed=False)
    res_unconfirmed = await require_human_confirmation(tool, {"router_id": "RTR-01"}, unconfirmed_ctx)
    assert res_unconfirmed is not None
    assert "ACTION STOPPED BY PROGRAMMATIC GUARDRAIL" in res_unconfirmed

    # Confirmed action passes through
    confirmed_ctx = DummyContext(confirmed=True)
    res_confirmed = await require_human_confirmation(tool, {"router_id": "RTR-01"}, confirmed_ctx)
    assert res_confirmed is None
