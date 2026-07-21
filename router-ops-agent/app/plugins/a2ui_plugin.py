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

"""A2UI Rendering and Image Artifact Interception Plugin for ADK Agents and Tools."""

import base64
import json
import logging
import re
from typing import Any

from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.adk.plugins import BasePlugin
from google.adk.tools import BaseTool, ToolContext
from google.genai import types

from app.models.callback_skips import CallbackSkips
from app.models.target_outputs import TargetOutput

logger = logging.getLogger("router-ops-agent.plugins.a2ui")


class A2UIPlugin(BasePlugin):
    """ADK Plugin that intercepts tool outputs for A2UI JSON rendering and image artifacts."""

    def __init__(self, name: str = "a2ui_plugin") -> None:
        """Initializes the A2UIPlugin instance.

        Args:
            name: Unique name identifier for the plugin.

        Returns:
            None.

        Raises:
            None.
        """
        super().__init__(name=name)

    async def after_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
        result: Any,
    ) -> Any:
        """Callback hook that intercepts individual tool results before returning to the planner.

        For tools returning A2UI JSON:
        - Bypasses LLM summarization latency by setting `tool_context.actions.skip_summarization = True`.
        - Returns the clean <a2ui-json> block.

        For tools returning Base64 PNGs:
        - Decodes and persists the image into the agent's artifact store.

        Args:
            tool: The executed tool instance.
            tool_args: Arguments passed to the tool.
            tool_context: Context for the current tool execution.
            result: Raw result returned by the tool.

        Returns:
            The processed result string or original result.

        Raises:
            None.
        """
        logger.setLevel(logging.DEBUG)
        logger.debug("In after_tool_callback:")
        for k, v in tool_args.items():
            logger.debug("tool_args[%s] = %s", k, v)

        tool_name = getattr(tool, "name", "")
        if tool_name in CallbackSkips:
            logger.debug("Skipping A2UI processing for %s", tool_name)
            return result

        if not self.has_content(result=result):
            logger.debug(
                "Skipping A2UI processing; no content for %s",
                tool_name,
            )
            return result

        raw_str = None
        first_item = result["content"][0]
        if not isinstance(first_item, dict):
            logger.debug(
                "Skipping A2UI processing; result content is not a dict: %s",
                first_item
            )
            return result

        for content in result["content"]:
            raw_str = content.get("text")
            match raw_str:
                case s if s and TargetOutput.DATA_IMAGE_PNG in s:
                    logger.debug("Intercepting image artifact for session artifact storage")
                    extracted = await self.intercept_image_artifact(
                        args=tool_args,
                        tool_context=tool_context,
                        raw_str=s,
                    )
                    logger.debug("Image artifact extracted: %s", extracted)
                    return extracted if extracted is not None else result

                case s if s and TargetOutput.A2UI_JSON in s:
                    logger.debug("Intercepting A2UI JSON card")
                    # Instruct ADK runner not to send this raw JSON to LLM for summarization
                    tool_context.actions.skip_summarization = True
                    match = re.search(r"<a2ui-json>(.*?)</a2ui-json>", s, re.DOTALL)
                    if match:
                        clean_output = match.group(1).strip()
                        return f"<a2ui-json>\n{clean_output}\n</a2ui-json>"

                case _:
                    logger.debug("No match for target string %s", raw_str)
                    continue

        return result

    async def on_event_callback(
        self,
        *,
        invocation_context: InvocationContext,
        event: Event,
    ) -> Event | None:
        """Consolidates single or multiple A2UI cards into a unified multi-card surface.

        Architectural Flow:
        1. Multi-Tool Scoping: When an agent calls multiple render tools in parallel within
           the same turn (e.g. `render_router_card(EAST-01)` and `render_router_card(EAST-02)`),
           `after_tool_callback` runs separately per tool.
        2. Event-Level Interception: `on_event_callback` intercepts the final turn Event containing
           all tool output parts after parallel execution completes.
        3. Solving A2UI Collisions:
           - Surface Overwrite: Emitting multiple `beginRendering` tags in one message causes the
             frontend to overwrite previous surfaces. We solve this by unifying into a single
             surface (`surfaceId: "unified-router-cards"`).
           - Component ID Collisions: Each MCP card uses identical component IDs (e.g. `card-root`).
             We scope component IDs by prefixing each card's components (`card_0_`, `card_1_`).
        4. Layout Composition: Wraps all scoped card roots in a shared top-level `Column` container
           so all cards render simultaneously stacked in the chat message.

        Args:
            invocation_context: The execution context for the current invocation.
            event: The final turn Event containing content parts generated by the runner.

        Returns:
            The modified Event with a single consolidated <a2ui-json> block, or the original event.

        Raises:
            None.
        """
        if not event.content or not event.content.parts:
            return event

        extracted_card_payloads: list[list[dict[str, Any]]] = []

        # 1. Collect all A2UI payloads from all tool parts in this turn
        for part in event.content.parts:
            text = getattr(part, "text", None)
            if not text:
                continue

            for match in re.finditer(r"<a2ui-json>(.*?)</a2ui-json>", text, re.DOTALL):
                try:
                    ops = json.loads(match.group(1).strip())
                    if isinstance(ops, list):
                        extracted_card_payloads.append(ops)
                except Exception as err:
                    logger.error("Error parsing A2UI JSON in on_event_callback: %s", err)

            # Strip the raw <a2ui-json> tags from message text parts to avoid leaking unrendered JSON
            part.text = re.sub(r"<a2ui-json>.*?</a2ui-json>", "", text, flags=re.DOTALL).strip()

        if not extracted_card_payloads:
            return event

        # 2. Single Card Case: Relay directly without modification
        if len(extracted_card_payloads) == 1:
            merged_payload = f"<a2ui-json>\n{json.dumps(extracted_card_payloads[0], indent=2)}\n</a2ui-json>"
            event.content.parts.append(types.Part.from_text(text=merged_payload))
            return event

        # 3. Multi-Card Case: Merge all cards into a single Column container with scoped component IDs
        unified_components: list[dict[str, Any]] = []
        card_root_ids: list[str] = []

        for idx, card_ops in enumerate(extracted_card_payloads):
            prefix = f"card_{idx}_"
            for op in card_ops:
                if "surfaceUpdate" in op:
                    components = op["surfaceUpdate"].get("components", [])
                    if not components:
                        continue

                    # Serialize to JSON string for efficient component ID remapping
                    comp_str = json.dumps(components)
                    orig_ids = [c["id"] for c in components if "id" in c]
                    orig_ids.sort(key=len, reverse=True)

                    # Prefix all component ID definitions and child references
                    for orig_id in orig_ids:
                        comp_str = comp_str.replace(f'"{orig_id}"', f'"{prefix}{orig_id}"')

                    prefixed_comps = json.loads(comp_str)
                    card_root_id = f"{prefix}card-root"
                    card_root_ids.append(card_root_id)
                    unified_components.extend(prefixed_comps)

        # 4. Insert the parent Column layout holding all card roots
        unified_components.insert(
            0,
            {
                "id": "multi-card-root",
                "component": {
                    "Column": {
                        "children": {
                            "explicitList": card_root_ids
                        },
                        "style": {
                            "gap": "16px",
                            "margin": "0px",
                            "padding": "0px"
                        }
                    }
                }
            }
        )

        # 5. Build the unified single-surface A2UI operation payload
        unified_payload = [
            {
                "beginRendering": {
                    "surfaceId": "unified-router-cards",
                    "root": "multi-card-root"
                }
            },
            {
                "surfaceUpdate": {
                    "surfaceId": "unified-router-cards",
                    "components": unified_components
                }
            }
        ]

        merged_str = f"<a2ui-json>\n{json.dumps(unified_payload, indent=2)}\n</a2ui-json>"
        event.content.parts.append(types.Part.from_text(text=merged_str))
        return event


    @staticmethod
    def has_content(result: Any) -> bool:
        """Checks if the tool result contains a non-empty content list.

        Args:
            result: Raw tool result payload.

        Returns:
            True if result is a dictionary containing a content list, False otherwise.

        Raises:
            None.
        """
        if (
            isinstance(result, dict)
            and result.get("content", None)
            and isinstance(result.get("content", None), list)
        ):
            return True
        return False

    @classmethod
    async def intercept_a2ui_tool(
        cls,
        tool: BaseTool,
        args: dict[str, Any],
        tool_context: ToolContext,
        tool_response: Any,
    ) -> Any | None:
        """Class method adapter forwarding to the pattern-matched callback logic.

        Args:
            tool: Target BaseTool instance executed by the planner.
            args: Dictionary of arguments passed to the tool function.
            tool_context: Execution ToolContext for session artifact and action management.
            tool_response: Raw response string or dictionary payload returned by the tool.

        Returns:
            Sanitized text response or clean A2UI JSON string, or None.

        Raises:
            None.
        """
        plugin = cls()
        processed = await plugin.after_tool_callback(
            tool=tool,
            tool_args=args,
            tool_context=tool_context,
            result=tool_response,
        )
        return processed

    @classmethod
    def extract_text(cls, tool_response: Any) -> str:
        """Extracts text content from a raw or dictionary-based tool response.

        Args:
            tool_response: The raw response object or dictionary returned by a tool.

        Returns:
            Normalized string representation of the tool output text.

        Raises:
            None.
        """
        if isinstance(tool_response, dict):
            content = tool_response.get("content", [])
            if content and isinstance(content, list):
                first_item = content[0]
                if isinstance(first_item, dict) and "text" in first_item:
                    return str(first_item["text"])
        return str(tool_response)

    @classmethod
    async def intercept_a2ui_card(
        cls,
        tool: BaseTool,
        tool_context: ToolContext,
        target_str: str,
    ) -> str:
        """Extracts clean A2UI JSON string block and sets skip_summarization = True.

        Args:
            tool: Target BaseTool instance executed by the planner.
            tool_context: Execution ToolContext for session action management.
            target_str: Normalized text string containing the tool response.

        Returns:
            Clean <a2ui-json> string block.

        Raises:
            None.
        """
        tool_name = getattr(tool, "name", "")
        logger.info("Found <a2ui-json> in tool '%s'. Enabling skip_summarization to bypass LLM relay latency.", tool_name)
        tool_context.actions.skip_summarization = True
        match = re.search(r"(<a2ui-json>.*?</a2ui-json>)", target_str, re.DOTALL)
        if match:
            clean_output = match.group(1).strip()
            logger.info("Returning cleaned <a2ui-json> block as string (length: %d).", len(clean_output))
            return clean_output
        return target_str

    @classmethod
    async def intercept_image_artifact(
        cls,
        args: dict[str, Any],
        tool_context: ToolContext,
        raw_str: str,
    ) -> str | None:
        """Extracts Base64 PNG image payloads, saves session artifacts, and returns an A2UI Image card.

        Args:
            args: Dictionary of arguments passed to the tool function.
            tool_context: Execution ToolContext for session artifact management.
            raw_str: Raw string containing the Base64 data URI.

        Returns:
            A2UI JSON string block wrapping the Image component, or None.

        Raises:
            None.
        """
        logger.debug("Checking for image in data")
        match = re.search(r"data:image/png;base64,([A-Za-z0-9+/=]+)", raw_str)
        if not match:
            logger.warning("Image not found; returning")
            return None

        b64_data = match.group(1)
        router_id = str(args.get("router_id") or "chassis").strip().upper()
        filename = f"router_card_{router_id.lower().replace('-', '_')}.png"

        try:
            logger.debug("Getting base64 encoded image")
            png_bytes = base64.b64decode(b64_data)

            logger.debug("Creating artifact part")
            artifact_part = types.Part.from_bytes(
                data=png_bytes, mime_type="image/png"
            )

            logger.debug("Saving artifact")
            await tool_context.save_artifact(filename=filename, artifact=artifact_part)
            logger.debug("Saved image snapshot artifact '%s'.", filename)
        except Exception as err:
            logger.error("Error saving image artifact in callback: %s", err)

        # Enable skip_summarization so the A2UI Image card passes directly to on_event_callback
        tool_context.actions.skip_summarization = True

        surface_id = f"router-card-image-{router_id.lower().replace('-', '_')}"
        a2ui_payload = [
            {
                "beginRendering": {
                    "surfaceId": surface_id,
                    "root": "card-root",
                }
            },
            {
                "surfaceUpdate": {
                    "surfaceId": surface_id,
                    "components": [
                        {
                            "id": "card-root",
                            "component": {
                                "Card": {
                                    "child": "image-comp",
                                    "style": {
                                        "backgroundColor": "#0B131E",
                                        "borderRadius": "12px",
                                        "padding": "8px",
                                    },
                                }
                            },
                        },
                        {
                            "id": "image-comp",
                            "component": {
                                "Image": {
                                    "url": {
                                        "literalString": f"data:image/png;base64,{b64_data}"
                                    },
                                    "fit": "contain",
                                }
                            },
                        },
                    ],
                }
            },
        ]
        return f"<a2ui-json>\n{json.dumps(a2ui_payload, indent=2)}\n</a2ui-json>"
