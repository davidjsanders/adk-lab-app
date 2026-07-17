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

"""Utility module to sanitize event payloads and format A2UI interactive cards for A2A / Agent Runtime."""

import json
import logging
import re
from enum import Enum
from typing import Any

from a2a.types import DataPart, Part, TaskArtifactUpdateEvent, TaskStatusUpdateEvent, TextPart

logger = logging.getLogger(__name__)

def sanitize_value(val: Any) -> Any:
    """Recursively converts non-serializable values (e.g. Enums) into primitive types."""
    match val:
        case Enum():
            return val.value
        case dict():
            return {k: sanitize_value(v) for k, v in val.items()}
        case list() | tuple():
            return [sanitize_value(x) for x in val]
        case _:
            return val

def _convert_a2ui_parts(parts: list[Any]) -> list[Any]:
    """Inspects text parts and transforms <a2ui-json> blocks into application/json+a2ui DataParts."""
    new_parts = []
    for part in parts:
        part_root = getattr(part, "root", part)
        if isinstance(part_root, TextPart) and part_root.text:
            text = part_root.text
            if "<a2ui-json>" in text and "</a2ui-json>" in text:
                logger.info("sanitize_events: Converting <a2ui-json> to application/json+a2ui DataPart")
                match = re.search(r"<a2ui-json>(.*?)</a2ui-json>", text, re.DOTALL)
                if match:
                    json_str = match.group(1).strip()
                    try:
                        parsed_json = json.loads(json_str)
                        if isinstance(parsed_json, list):
                            for msg in parsed_json:
                                new_parts.append(
                                    Part(
                                        root=DataPart(
                                            data=sanitize_value(msg),
                                            metadata={"mimeType": "application/json+a2ui"},
                                        )
                                    )
                                )
                        else:
                            new_parts.append(
                                Part(
                                    root=DataPart(
                                        data=sanitize_value(parsed_json),
                                        metadata={"mimeType": "application/json+a2ui"},
                                    )
                                )
                            )
                        continue
                    except Exception as e:
                        logger.error(f"Error parsing <a2ui-json> during event sanitization: {e}")
        new_parts.append(part)
    return new_parts

def sanitize_event(event: Any) -> None:
    """Sanitizes an A2A event in-place and converts A2UI JSON blocks."""
    if hasattr(event, "metadata") and event.metadata:
        event.metadata = sanitize_value(event.metadata)

    if isinstance(event, TaskStatusUpdateEvent) and event.status and event.status.message:
        if event.status.message.metadata:
            event.status.message.metadata = sanitize_value(event.status.message.metadata)
        if event.status.message.parts:
            event.status.message.parts = _convert_a2ui_parts(event.status.message.parts)
            for part in event.status.message.parts:
                if hasattr(part, "root") and part.root:
                    if hasattr(part.root, "data") and part.root.data:
                        part.root.data = sanitize_value(part.root.data)
                    if hasattr(part.root, "metadata") and part.root.metadata:
                        part.root.metadata = sanitize_value(part.root.metadata)

    if isinstance(event, TaskArtifactUpdateEvent) and event.artifact:
        if event.artifact.metadata:
            event.artifact.metadata = sanitize_value(event.artifact.metadata)
        if event.artifact.parts:
            event.artifact.parts = _convert_a2ui_parts(event.artifact.parts)
            for part in event.artifact.parts:
                if hasattr(part, "root") and part.root:
                    if hasattr(part.root, "data") and part.root.data:
                        part.root.data = sanitize_value(part.root.data)
                    if hasattr(part.root, "metadata") and part.root.metadata:
                        part.root.metadata = sanitize_value(part.root.metadata)

async def sanitize_after_event(executor_context: Any, a2a_event: Any, adk_event: Any) -> Any:
    """Interceptor called after an intermediate event is generated."""
    sanitize_event(a2a_event)
    return a2a_event

async def sanitize_after_agent(executor_context: Any, final_event: Any) -> Any:
    """Interceptor called after the final agent response is generated."""
    sanitize_event(final_event)
    return final_event
