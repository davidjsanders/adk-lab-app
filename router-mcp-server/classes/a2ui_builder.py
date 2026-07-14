"""A2UI v0.8 Declarative Snapshot UI Card Builder Class."""

from typing import Any, Dict, Optional


class A2UIBuilder:
    """Constructs clean A2UI v0.8 declarative manifests for router nodes."""

    @staticmethod
    def build_card_manifest(r_data: Dict[str, Any], default_id: Optional[str] = None) -> str:
        """Constructs a clean A2UI v0.8 declarative manifest for rendering a compact router card snapshot.

        Args:
            r_data: Router state dictionary containing ID, name, status, telemetry, uptime, etc.
            default_id: Fallback router string ID if r_data dictionary lacks an 'id' field.

        Returns:
            String containing <a2ui-json> enclosed payload.

        Raises:
            None.
        """
        r_id = r_data.get("id") or default_id or "UNKNOWN"
        r_name = r_data.get("name") or r_data.get("display_name") or r_id
        location = r_data.get("location") or r_data.get("location_description") or "N/A"
        state = str(r_data.get("state") or r_data.get("status") or "OPERATIONAL").upper()
        uptime = r_data.get("uptime_seconds") or r_data.get("uptime") or 0
        mfg = r_data.get("manufacturer") or "Cisco Systems"
        model = r_data.get("model") or "C8500-12X4QC"
        deployed = r_data.get("last_deployed") or "N/A"
        revision = r_data.get("revision") or "N/A"
        leds = r_data.get("leds", {})

        # Build static LED indicator status string snapshot
        led_icons = []
        for led_name in ["pwr", "online", "upstream", "lan1", "lan2", "lan3", "lan4", "send", "recv"]:
            color = str(leds.get(led_name, "OFF")).upper()
            icon = "🟢" if "GREEN" in color else "🟠" if "AMBER" in color else "🔴" if "RED" in color else "⚫"
            led_icons.append(f"{led_name.upper()}:{icon}")

        led_summary = "  ".join(led_icons)
        surface_id = f"router-card-{r_id.lower().replace('-', '_')}"

        payload = [
            {
                "beginRendering": {
                    "surfaceId": surface_id,
                    "root": "card-root"
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
                                    "child": "main-col"
                                }
                            }
                        },
                        {
                            "id": "main-col",
                            "component": {
                                "Column": {
                                    "children": {
                                        "explicitList": ["hdr-row", "sub-hdr", "telemetry-box", "led-box", "btn-row"]
                                    }
                                }
                            }
                        },
                        {
                            "id": "hdr-row",
                            "component": {
                                "Row": {
                                    "children": {
                                        "explicitList": ["title-text", "badge-text"]
                                    }
                                }
                            }
                        },
                        {
                            "id": "title-text",
                            "component": {
                                "Text": {
                                    "usageHint": "h2",
                                    "text": {"literalString": f"{r_name}"}
                                }
                            }
                        },
                        {
                            "id": "badge-text",
                            "component": {
                                "Text": {
                                    "usageHint": "caption",
                                    "text": {"literalString": f" [{state}]"}
                                }
                            }
                        },
                        {
                            "id": "sub-hdr",
                            "component": {
                                "Text": {
                                    "usageHint": "body2",
                                    "text": {"literalString": f"ID: {r_id} • Location: {location}"}
                                }
                            }
                        },
                        {
                            "id": "telemetry-box",
                            "component": {
                                "Column": {
                                    "children": {
                                        "explicitList": ["t-line-1", "t-line-2", "t-line-3"]
                                    }
                                }
                            }
                        },
                        {
                            "id": "t-line-1",
                            "component": {
                                "Text": {
                                    "usageHint": "monospace",
                                    "text": {"literalString": f"UPTIME: {uptime}s | STATE: {state}"}
                                }
                            }
                        },
                        {
                            "id": "t-line-2",
                            "component": {
                                "Text": {
                                    "usageHint": "monospace",
                                    "text": {"literalString": f"MFG/MODEL: {mfg} {model}"}
                                }
                            }
                        },
                        {
                            "id": "t-line-3",
                            "component": {
                                "Text": {
                                    "usageHint": "monospace",
                                    "text": {"literalString": f"DEPLOYED: {deployed} | REV: {revision}"}
                                }
                            }
                        },
                        {
                            "id": "led-box",
                            "component": {
                                "Text": {
                                    "usageHint": "body1",
                                    "text": {"literalString": f"LED Status: {led_summary}"}
                                }
                            }
                        },
                        {
                            "id": "btn-row",
                            "component": {
                                "Row": {
                                    "children": {
                                        "explicitList": ["btn-pwr", "btn-rst", "btn-bgp"]
                                    }
                                }
                            }
                        },
                        {
                            "id": "btn-pwr",
                            "component": {
                                "Button": {
                                    "child": "btn-pwr-lbl",
                                    "action": {
                                        "name": "send_router_command",
                                        "parameters": {"router_id": r_id, "action": "POWER_TOGGLE"}
                                    }
                                }
                            }
                        },
                        {
                            "id": "btn-pwr-lbl",
                            "component": {
                                "Text": {"text": {"literalString": "Toggle Power"}}
                            }
                        },
                        {
                            "id": "btn-rst",
                            "component": {
                                "Button": {
                                    "child": "btn-rst-lbl",
                                    "action": {
                                        "name": "send_router_command",
                                        "parameters": {"router_id": r_id, "action": "REBOOT"}
                                    }
                                }
                            }
                        },
                        {
                            "id": "btn-rst-lbl",
                            "component": {
                                "Text": {"text": {"literalString": "Reboot System"}}
                            }
                        },
                        {
                            "id": "btn-bgp",
                            "component": {
                                "Button": {
                                    "child": "btn-bgp-lbl",
                                    "action": {
                                        "name": "send_router_command",
                                        "parameters": {"router_id": r_id, "action": "BGP_RESET"}
                                    }
                                }
                            }
                        },
                        {
                            "id": "btn-bgp-lbl",
                            "component": {
                                "Text": {"text": {"literalString": "Reset BGP Session"}}
                            }
                        }
                    ]
                }
            }
        ]

        import json
        return f"<a2ui-json>\n{json.dumps(payload, indent=2)}\n</a2ui-json>"


def build_a2ui_router_card_manifest(r_data: Dict[str, Any], default_id: Optional[str] = None) -> str:
    """Top-level functional wrapper for A2UIBuilder.build_card_manifest.

    Args:
        r_data: Router state dictionary containing ID, name, status, telemetry, uptime, etc.
        default_id: Fallback router string ID if r_data dictionary lacks an 'id' field.

    Returns:
        String containing <a2ui-json> enclosed payload.

    Raises:
        None.
    """
    return A2UIBuilder.build_card_manifest(r_data, default_id=default_id)
