import json
import logging
import re
from typing import Any

from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.adk.plugins import BasePlugin
from google.adk.tools import BaseTool, ToolContext
from google.genai import types

logger = logging.getLogger("sysman-detection-agent.plugins.a2ui")


class A2UIPlugin(BasePlugin):
    """Surgical plugin that intercepts A2UI card outputs to bypass LLM summarization latency."""

    def __init__(self, name: str = "a2ui_plugin") -> None:
        super().__init__(name=name)
        self._pending_cards: dict[str, list[str]] = {}

    async def after_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
        result: Any,
    ) -> Any:
        """Intercepts tool output to parse <a2ui-json> and bypass LLM summarization.

        Args:
            tool: BaseTool executed.
            tool_args: Arguments passed.
            tool_context: ToolContext.
            result: Raw result.

        Returns:
            Sanitized or original result.
        """
        session_id = getattr(tool_context, "session_id", "default")
        text = ""
        is_dict_content = False
        
        if isinstance(result, dict) and result.get("content") and isinstance(result["content"], list):
            first_item = result["content"][0]
            if isinstance(first_item, dict):
                text = first_item.get("text", "")
                is_dict_content = True
        else:
            text = str(result)

        if "<a2ui-json>" in text:
            # Tell ADK runner not to summarize the JSON component tree
            tool_context.actions.skip_summarization = True
            
            # Find and extract the A2UI blocks to store them in pending queue
            matches = re.findall(r"(<a2ui-json>.*?</a2ui-json>)", text, re.DOTALL)
            if matches:
                if session_id not in self._pending_cards:
                    self._pending_cards[session_id] = []
                self._pending_cards[session_id].extend(matches)
                
                # Strip the A2UI blocks from the text to return ONLY the plain text summary to the LLM
                clean_text = re.sub(r"<a2ui-json>.*?</a2ui-json>", "", text, flags=re.DOTALL).strip()
                return clean_text

        return result

    async def on_event_callback(
        self,
        *,
        invocation_context: InvocationContext,
        event: Event,
    ) -> Event | None:
        """Consolidates single or multiple A2UI cards into a unified multi-card surface."""
        session_id = getattr(invocation_context, "session_id", "default")
        
        if not event.content or not event.content.parts:
            # Even if there is no event content generated yet, if we have pending cards, we must inject them
            if session_id in self._pending_cards and self._pending_cards[session_id]:
                event.content = types.Content(role="model", parts=[])
            else:
                return event

        extracted_card_payloads: list[list[dict[str, Any]]] = []

        # 1. Collect all A2UI payloads from event parts (if the agent generated any raw ones)
        for part in event.content.parts:
            text = self._extract_part_text(part)
            if not text:
                continue

            for match in re.finditer(r"<a2ui-json>(.*?)</a2ui-json>", text, re.DOTALL):
                try:
                    ops = json.loads(match.group(1).strip())
                    if isinstance(ops, list):
                        extracted_card_payloads.append(ops)
                except Exception as err:
                    logger.error("Error parsing A2UI JSON in on_event_callback: %s", err)

        # 2. Append any pending cards stored during the tool execution in this session
        if session_id in self._pending_cards:
            for card_str in self._pending_cards[session_id]:
                for match in re.finditer(r"<a2ui-json>(.*?)</a2ui-json>", card_str, re.DOTALL):
                    try:
                        ops = json.loads(match.group(1).strip())
                        if isinstance(ops, list):
                            extracted_card_payloads.append(ops)
                    except Exception as err:
                        logger.error("Error parsing stored A2UI JSON: %s", err)
            # Clear pending cards for this session after consuming them
            del self._pending_cards[session_id]

        # 3. Deduplicate identical card payloads
        unique_payloads: list[list[dict[str, Any]]] = []
        seen_surfaces: set[str] = set()

        for card_ops in extracted_card_payloads:
            surface_id = None
            for op in card_ops:
                if "beginRendering" in op:
                    surface_id = op["beginRendering"].get("surfaceId")
                    break
                if "surfaceUpdate" in op:
                    surface_id = op["surfaceUpdate"].get("surfaceId")
                    break
            if surface_id:
                if surface_id in seen_surfaces:
                    continue
                seen_surfaces.add(surface_id)
            unique_payloads.append(card_ops)

        extracted_card_payloads = unique_payloads

        if not extracted_card_payloads:
            return event

        # 4. Strip raw unmerged <a2ui-json> tags from event parts
        for part in event.content.parts:
            if hasattr(part, "text") and part.text:
                part.text = re.sub(r"<a2ui-json>.*?</a2ui-json>", "", part.text, flags=re.DOTALL).strip()
            elif hasattr(part, "function_response") and part.function_response:
                resp = getattr(part.function_response, "response", None)
                if isinstance(resp, dict) and "result" in resp and isinstance(resp["result"], str):
                    resp["result"] = re.sub(r"<a2ui-json>.*?</a2ui-json>", "", resp["result"], flags=re.DOTALL).strip()

        # 5. Merge all cards into a single Column container or handle single card case
        if len(extracted_card_payloads) == 1:
            card_ops = extracted_card_payloads[0]
            merged_str = f"<a2ui-json>\n{json.dumps(card_ops, indent=2)}\n</a2ui-json>"
            event.content.parts.append(types.Part.from_text(text=merged_str))
            return event

        # Multi-Card Case: Merge all cards into a single Column container with scoped component IDs
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

        # Insert the parent Column layout holding all card roots
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

        # Build the unified single-surface A2UI operation payload
        unified_payload = [
            {
                "beginRendering": {
                    "surfaceId": "unified-system-cards",
                    "root": "multi-card-root"
                }
            },
            {
                "surfaceUpdate": {
                    "surfaceId": "unified-system-cards",
                    "components": unified_components
                }
            }
        ]

        merged_str = f"<a2ui-json>\n{json.dumps(unified_payload, indent=2)}\n</a2ui-json>"
        event.content.parts.append(types.Part.from_text(text=merged_str))
        return event

    @staticmethod
    def _extract_part_text(part: Any) -> str:
        if hasattr(part, "text") and part.text:
            return part.text
        if hasattr(part, "function_response") and part.function_response:
            resp = getattr(part.function_response, "response", None)
            if isinstance(resp, str):
                return resp
            elif isinstance(resp, dict):
                if "result" in resp and isinstance(resp["result"], str):
                    return resp["result"]
                if "content" in resp and isinstance(resp["content"], list):
                    texts = []
                    for item in resp["content"]:
                        if isinstance(item, dict) and "text" in item:
                            texts.append(str(item["text"]))
                    if texts:
                        return "\n".join(texts)
                return json.dumps(resp)
        return ""
