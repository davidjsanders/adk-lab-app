"""Unit tests for A2A post-event interceptor conversion utilities."""

from unittest.mock import MagicMock

import pytest
from a2a.types import (
    Artifact,
    DataPart,
    Message,
    Part,
    TaskArtifactUpdateEvent,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)

from app.app_utils.a2a import _a2ui_after_event


@pytest.mark.asyncio
async def test_a2ui_after_event_converts_valid_json():
    """Verifies that valid <a2ui-json> blocks are converted into A2A FileParts."""
    payload = '[{"beginRendering": {"surfaceId": "test"}}]'
    msg = Message(
        messageId="msg-1",
        role="agent",
        parts=[Part(root=TextPart(text=f"<a2ui-json>\n{payload}\n</a2ui-json>"))],
    )
    event = TaskStatusUpdateEvent(
        taskId="task-1",
        contextId="ctx-1",
        status=TaskStatus(state="working", message=msg),
        final=False,
    )
    ctx = MagicMock()

    mutated_event = await _a2ui_after_event(ctx, event, None)

    assert mutated_event.status.message.parts[0].root.kind == "data"
    data_part = mutated_event.status.message.parts[0].root
    assert isinstance(data_part, DataPart)
    assert data_part.metadata == {"mimeType": "application/json+a2ui"}
    assert data_part.data == {"beginRendering": {"surfaceId": "test"}}


@pytest.mark.asyncio
async def test_a2ui_after_event_ignores_normal_text():
    """Verifies that standard TextParts without <a2ui-json> tags are left untouched."""
    msg = Message(
        messageId="msg-1",
        role="agent",
        parts=[Part(root=TextPart(text="Hello world"))],
    )
    event = TaskStatusUpdateEvent(
        taskId="task-1",
        contextId="ctx-1",
        status=TaskStatus(state="working", message=msg),
        final=False,
    )
    ctx = MagicMock()

    mutated_event = await _a2ui_after_event(ctx, event, None)

    assert mutated_event.status.message.parts[0].root.kind == "text"
    text_part = mutated_event.status.message.parts[0].root
    assert isinstance(text_part, TextPart)
    assert text_part.text == "Hello world"


@pytest.mark.asyncio
async def test_a2ui_after_event_artifact_update_event():
    """Verifies that TaskArtifactUpdateEvent parts containing <a2ui-json> are also converted."""
    payload = '[{"beginRendering": {"surfaceId": "art"}}]'
    artifact = Artifact(
        artifactId="art-1",
        parts=[Part(root=TextPart(text=f"<a2ui-json>{payload}</a2ui-json>"))],
    )
    event = TaskArtifactUpdateEvent(
        taskId="task-1",
        contextId="ctx-1",
        artifact=artifact,
        lastChunk=True,
    )
    ctx = MagicMock()

    mutated_event = await _a2ui_after_event(ctx, event, None)

    assert mutated_event.artifact.parts[0].root.kind == "data"
    data_part = mutated_event.artifact.parts[0].root
    assert isinstance(data_part, DataPart)
    assert data_part.metadata == {"mimeType": "application/json+a2ui"}
    assert data_part.data == {"beginRendering": {"surfaceId": "art"}}
