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

logger = logging.getLogger("router-agent.helpers.callbacks")


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
    if not tool_response:
        return None

    raw_str = str(tool_response)

    # 1. Base64 Image Card Snapshot Artifact Interception
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
