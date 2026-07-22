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

"""Unit tests for the A2UI plugin."""

import json
from unittest.mock import MagicMock

import pytest
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.adk.tools import ToolContext
from google.genai import types

from app.plugins.a2ui_plugin import A2UIPlugin


@pytest.mark.asyncio
async def test_has_content() -> None:
    """Tests has_content validation for various result formats.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError if test expectations fail.
    """
    assert A2UIPlugin.has_content({"content": [{"text": "hello"}]}) is True
    assert A2UIPlugin.has_content({}) is False
    assert A2UIPlugin.has_content("not a dict") is False


@pytest.mark.asyncio
async def test_after_tool_callback_a2ui_json() -> None:
    """Tests after_tool_callback intercepts and extracts A2UI JSON payloads.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError if test expectations fail.
    """
    plugin = A2UIPlugin()
    tool = MagicMock()
    tool.name = "render_router_card"

    tool_context = MagicMock(spec=ToolContext)
    tool_context.actions = MagicMock()

    raw_json = '[{"beginRendering": {"surfaceId": "test", "root": "card-root"}}]'
    result = {"content": [{"text": f"<a2ui-json>\n{raw_json}\n</a2ui-json>"}]}

    res = await plugin.after_tool_callback(
        tool=tool,
        tool_args={"router_id": "EAST-01"},
        tool_context=tool_context,
        result=result,
    )

    assert tool_context.actions.skip_summarization is True
    assert "<a2ui-json>" in res
    assert "surfaceId" in res


@pytest.mark.asyncio
async def test_on_event_callback_multi_card() -> None:
    """Tests multi-card consolidation into a single Column surface in on_event_callback.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError if test expectations fail.
    """
    plugin = A2UIPlugin()
    inv_context = MagicMock(spec=InvocationContext)

    card1 = json.dumps([
        {"beginRendering": {"surfaceId": "s1", "root": "card-root"}},
        {"surfaceUpdate": {"surfaceId": "s1", "components": [{"id": "card-root"}]}},
    ])
    card2 = json.dumps([
        {"beginRendering": {"surfaceId": "s2", "root": "card-root"}},
        {"surfaceUpdate": {"surfaceId": "s2", "components": [{"id": "card-root"}]}},
    ])

    part1 = types.Part.from_text(text=f"<a2ui-json>\n{card1}\n</a2ui-json>")
    part2 = types.Part.from_text(text=f"<a2ui-json>\n{card2}\n</a2ui-json>")

    content = types.Content(parts=[part1, part2])
    event = Event(content=content)

    updated_event = await plugin.on_event_callback(
        invocation_context=inv_context,
        event=event,
    )

    assert updated_event is not None
    last_part = updated_event.content.parts[-1]
    assert "<a2ui-json>" in last_part.text
    assert "unified-router-cards" in last_part.text
    assert "card_0_card-root" in last_part.text
    assert "card_1_card-root" in last_part.text


@pytest.mark.asyncio
async def test_after_tool_callback_image_artifact() -> None:
    """Tests after_tool_callback saves image artifact and returns A2UI Image card payload.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError if test expectations fail.
    """
    plugin = A2UIPlugin()
    tool = MagicMock()
    tool.name = "render_router_card_image"

    tool_context = MagicMock(spec=ToolContext)
    tool_context.actions = MagicMock()

    img_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    result = {"content": [{"text": f"data:image/png;base64,{img_b64}"}]}

    res = await plugin.after_tool_callback(
        tool=tool,
        tool_args={"router_id": "RTR-CAN-ATLANTIC-01"},
        tool_context=tool_context,
        result=result,
    )

    assert tool_context.actions.skip_summarization is True
    assert "<a2ui-json>" in res
    assert "router-card-image-rtr_can_atlantic_01" in res


@pytest.mark.asyncio
async def test_on_event_callback_function_response_merge() -> None:
    """Tests multi-card consolidation from FunctionResponse parts in on_event_callback.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError if test expectations fail.
    """
    plugin = A2UIPlugin()
    inv_context = MagicMock(spec=InvocationContext)

    card1 = json.dumps([
        {"beginRendering": {"surfaceId": "s1", "root": "card-root"}},
        {"surfaceUpdate": {"surfaceId": "s1", "components": [{"id": "card-root"}]}},
    ])
    card2 = json.dumps([
        {"beginRendering": {"surfaceId": "s2", "root": "card-root"}},
        {"surfaceUpdate": {"surfaceId": "s2", "components": [{"id": "card-root"}]}},
    ])

    fr1 = types.FunctionResponse(name="f1", response={"result": f"<a2ui-json>\n{card1}\n</a2ui-json>"})
    fr2 = types.FunctionResponse(name="f2", response={"result": f"<a2ui-json>\n{card2}\n</a2ui-json>"})

    part1 = types.Part(function_response=fr1)
    part2 = types.Part(function_response=fr2)

    content = types.Content(parts=[part1, part2])
    event = Event(content=content)

    updated_event = await plugin.on_event_callback(
        invocation_context=inv_context,
        event=event,
    )

    assert updated_event is not None
    last_part = updated_event.content.parts[-1]
    assert "<a2ui-json>" in last_part.text
    assert "unified-router-cards" in last_part.text
    assert "card_0_card-root" in last_part.text
    assert "card_1_card-root" in last_part.text


@pytest.mark.asyncio
async def test_on_event_callback_dedup_single_router() -> None:
    """Tests that duplicate card payloads for the same surfaceId are deduplicated.

    Args:
        None.

    Returns:
        None.

    Raises:
        AssertionError if test expectations fail.
    """
    plugin = A2UIPlugin()
    inv_context = MagicMock(spec=InvocationContext)

    card = json.dumps([
        {"beginRendering": {"surfaceId": "router-card-rtr-can-east-02", "root": "card-root"}},
        {"surfaceUpdate": {"surfaceId": "router-card-rtr-can-east-02", "components": [{"id": "card-root"}]}},
    ])

    fr = types.FunctionResponse(name="f1", response={"result": f"<a2ui-json>\n{card}\n</a2ui-json>"})
    part_fr = types.Part(function_response=fr)
    part_txt = types.Part.from_text(text=f"<a2ui-json>\n{card}\n</a2ui-json>")

    content = types.Content(parts=[part_fr, part_txt])
    event = Event(content=content)

    updated_event = await plugin.on_event_callback(
        invocation_context=inv_context,
        event=event,
    )

    # Should deduplicate to 1 single card and return event without adding unified multi-card wrapper
    assert len(updated_event.content.parts) == 2
    assert "unified-router-cards" not in str(updated_event.content.parts)



