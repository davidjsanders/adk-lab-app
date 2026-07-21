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

"""ADK Agent Callback Functions.

Contains tool interception hooks for extracting base64 image payloads into
ADK session artifacts and sanitizing LLM context window token overhead.
"""

import base64
import logging
import re
from typing import Any

from google.adk.tools import BaseTool, ToolContext
from google.genai import types

logger = logging.getLogger("router-ops-agent.helpers.callbacks")


async def intercept_image_card_tool(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: Any,
) -> Any | None:
    """Intercepts tool responses, saves Base64 PNG images to ADK session artifacts, and truncates token context passed to the LLM model.

    Args:
        tool: Target BaseTool instance executed by the planner.
        args: Dictionary of arguments passed to the tool function.
        tool_context: Execution ToolContext for session artifact management.
        tool_response: Raw response string or dictionary payload returned by the tool.

    Returns:
        Sanitized text response string with Base64 payloads replaced by artifact markers, or None.

    Raises:
        None.
    """
    logger.setLevel(logging.DEBUG)

    logger.debug("Callback called on tool %s", tool)
    tool_name = getattr(tool, "name", "")
    logger.debug("tool name %s", tool_name)

    # NEVER intercept skill meta-tools or agent transfer tools
    if tool_name in ("list_skills", "load_skill", "load_skill_resource", "transfer_to_agent"):
        logger.debug("Skipping tool %s", tool_name)
        return None

    logger.info(f"intercept_image_card_tool called on tool '{tool_name}' with response type: {type(tool_response)}")
    raw_str = str(tool_response)
    # Try to extract clean string from FastMCP dict structure to avoid escaped newlines in str(dict)
    target_str = raw_str

    if isinstance(tool_response, dict):
        content = tool_response.get("content", [])
        if content and isinstance(content, list):
            first_item = content[0]
            if isinstance(first_item, dict) and "text" in first_item:
                target_str = first_item["text"]
                logger.info("Extracted target string from FastMCP content.")

    # 1. A2UI JSON Card Interception (Bypassing LLM Relay Latency)
    if "<a2ui-json>" in target_str:
        logger.info("Found <a2ui-json> in target string. Enabling skip_summarization to bypass LLM relay latency.")
        tool_context.actions.skip_summarization = False

        # Extract just the <a2ui-json> block to ensure clean output for the UI
        match = re.search(r"(<a2ui-json>.*?</a2ui-json>)", target_str, re.DOTALL)
        if match:
            clean_output = match.group(1).strip()
            logger.info(f"Returning cleaned <a2ui-json> block as string (length: {len(clean_output)}).")
            return clean_output

        logger.warning("Regex failed to extract <a2ui-json> block despite substring match.")
        # Fallback if regex fails but substring found
        return target_str

    # 2. Base64 Image Card Snapshot Artifact Interception
    if "data:image/png;base64," in raw_str:
        match = re.search(r"data:image/png;base64,([A-Za-z0-9+/=]+)", raw_str)
        if match:
            b64_data = match.group(1)
            try:
                png_bytes = base64.b64decode(b64_data)
                router_id = str(args.get("router_id") or "chassis").strip().upper()
                filename = f"router_card_{router_id.lower().replace('-', '_')}.png"

                # Save binary image artifact to ADK session storage
                artifact_part = types.Part.from_bytes(
                    data=png_bytes, mime_type="image/png"
                )
                await tool_context.save_artifact(
                    filename=filename, artifact=artifact_part
                )
                logger.info(
                    f"Extracted Base64 image payload and saved ADK session artifact '{filename}'."
                )

                # Return a clean confirmation text for the LLM context turn.
                return f"Successfully rendered visual card for router {router_id}. Saved image snapshot artifact '{filename}'."
            except Exception as err:
                logger.error(f"Error saving image artifact in callback: {err}")

    return None
