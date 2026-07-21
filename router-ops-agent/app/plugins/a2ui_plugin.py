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

from google.adk.plugins import BasePlugin
from google.adk.tools import BaseTool, ToolContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.genai import types

from app.models.callback_skips import CallbackSkips
from app.models.target_outputs import TargetOutput


logger = logging.getLogger("router-ops-agent.plugins.a2ui")


class A2UIPlugin(BasePlugin):
    """ADK Plugin that intercepts tool outputs for A2UI JSON rendering and image artifacts."""
    def __init__(self, name: str = "a2ui_plugin"):
        """Initializes the A2UIPlugin instance.

        Args:
            name: Unique name identifier for the plugin.
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
        """Callback hook using structural pattern matching to route tool responses.

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
        for k,v in tool_args.items():
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

        a2ui_canvas = []
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
                    tool_context.actions.skip_summarization = True
                    match = re.search(r"(<a2ui-json>(.*?)</a2ui-json>)", s, re.DOTALL)
                    if match:
                        clean_output = match.group(2).strip()
                        logger.debug("A2UI JSON extracted: %s", clean_output)
                        a2ui_canvas.append(clean_output)

                case _:
                    logger.debug("No match for target string %s", raw_str)
                    continue

        if a2ui_canvas:
            return "<a2ui-json>\n"+"\n".join(a2ui_canvas)+"\n</a2ui-json>\n"

        # raw_str = first_item.get("text")
        # target_str = raw_str

        # match target_str:
        #     case s if s and TargetOutput.DATA_IMAGE_PNG in s:
        #         logger.debug("Intercepting image artifact for session artifact storage")
        #         extracted = await self.intercept_image_artifact(
        #             args=tool_args,
        #             tool_context=tool_context,
        #             raw_str=s,
        #         )
        #         logger.debug("Image artifact extracted: %s", extracted)
        #         return extracted if extracted is not None else result

        #     case s if s and TargetOutput.A2UI_JSON in s:
        #         logger.debug("Intercepting A2UI JSON card")
        #         extracted = await self.intercept_a2ui_card(
        #             tool=tool,
        #             tool_context=tool_context,
        #             target_str=s,
        #         )
        #         logger.debug("A2UI JSON extracted: %s", extracted)
        #         return extracted if extracted is not None else result
        #     case _:
        #         logger.debug("No match for target string %s", target_str)
        #         return result

    async def on_event_callback(
        self,
        *,
        invocation_context: InvocationContext,
        event: Event,
    ) -> Event | None:
        """Consolidates multiple <a2ui-json> blocks across all event parts into a single A2UI block.

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

        all_operations: list[dict[str, Any]] = []
        has_a2ui = False

        for part in event.content.parts:
            text = getattr(part, "text", None)
            if not text:
                continue

            # Extract all <a2ui-json> payloads in this part (group 1 is the inner JSON)
            for match in re.finditer(r"<a2ui-json>(.*?)</a2ui-json>", text, re.DOTALL):
                has_a2ui = True
                clean_json_str = match.group(1).strip()
                try:
                    ops = json.loads(clean_json_str)
                    if isinstance(ops, list):
                        all_operations.extend(ops)
                    elif isinstance(ops, dict):
                        all_operations.append(ops)
                except Exception as err:
                    logger.error("Failed to parse A2UI JSON in on_event_callback: %s", err)

            # Strip the original <a2ui-json> blocks from the text part
            part.text = re.sub(r"<a2ui-json>.*?</a2ui-json>", "", text, flags=re.DOTALL).strip()

        # If any A2UI blocks were found, append a single consolidated <a2ui-json> block
        if has_a2ui and all_operations:
            merged_payload = f"<a2ui-json>\n{json.dumps(all_operations, indent=2)}\n</a2ui-json>"
            event.content.parts.append(types.Part.from_text(text=merged_payload))

        return event


    @staticmethod
    def has_content(result: Any) -> bool:
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
        """Extracts Base64 PNG image payloads and saves them as session artifacts.

        Args:
            args: Dictionary of arguments passed to the tool function.
            tool_context: Execution ToolContext for session artifact management.
            raw_str: Raw string containing the Base64 data URI.

        Returns:
            Sanitized confirmation string if an image was saved, or None.

        Raises:
            None.
        """
        logger.debug("Checking for image in data")
        match = re.search(r"data:image/png;base64,([A-Za-z0-9+/=]+)", raw_str)
        if not match:
            logger.warning("Image not found; returning")
            return None

        b64_data = match.group(1)
        try:
            logger.debug("Getting base64 encoded image")
            png_bytes = base64.b64decode(b64_data)

            logger.debug("Getting router ID")
            router_id = str(args.get("router_id") or "chassis").strip().upper()

            filename = f"router_card_{router_id.lower().replace('-', '_')}.png"
            logger.debug("Filename: %s", filename)

            logger.debug("Creating artifact part")
            artifact_part = types.Part.from_bytes(
                data=png_bytes, mime_type="image/png"
            )

            logger.debug("Saving artifact")
            await tool_context.save_artifact(filename=filename, artifact=artifact_part)

            logger.debug("Saved image snapshot artifact '%s'.", filename)
            return (
                f"Successfully rendered visual card for router {router_id}. "
                f"Saved image snapshot artifact '{filename}'."
            )
        except Exception as err:
            logger.error("Error saving image artifact in callback: %s", err)
            return None
