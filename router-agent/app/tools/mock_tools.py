import json
import logging

logger = logging.getLogger("router-agent.mock_tools")

# ============================================================================
# 1. Known-Working A2UI v0.8 Payload (Verified rendering in ADK Web UI)
# ============================================================================
WORKING_V08_A2UI_PAYLOAD = [
    {
        "beginRendering": {
            "surfaceId": "router-card-rtr_can_atlantic_01",
            "root": "card-root",
        }
    },
    {
        "surfaceUpdate": {
            "surfaceId": "router-card-rtr_can_atlantic_01",
            "components": [
                {
                    "id": "card-root",
                    "component": {
                        "Card": {
                            "child": "main-column",
                            "style": {
                                "backgroundColor": "#0B131E",
                                "borderRadius": "12px",
                            },
                        }
                    },
                },
                {
                    "id": "main-column",
                    "component": {
                        "Column": {
                            "children": {
                                "explicitList": [
                                    "header-title",
                                    "header-subtitle",
                                    "divider-1",
                                    "info-row-1",
                                    "info-row-2",
                                    "divider-2",
                                    "status-bar",
                                ]
                            },
                            "align": "stretch",
                        }
                    },
                },
                {
                    "id": "header-title",
                    "component": {
                        "Text": {
                            "text": {"literalString": "RTR-CAN-ATLANTIC-01"},
                            "variant": "h3",
                            "usageHint": "h3",
                            "style": {"color": "#00B0FF"},
                        }
                    },
                },
                {
                    "id": "header-subtitle",
                    "component": {
                        "Text": {
                            "text": {
                                "literalString": "Atlantic Hub Gateway 01 - Halifax NS"
                            },
                            "variant": "caption",
                            "usageHint": "caption",
                            "style": {"color": "#00B0FF"},
                        }
                    },
                },
                {"id": "divider-1", "component": {"Divider": {"axis": "horizontal"}}},
                {
                    "id": "info-row-1",
                    "component": {
                        "Text": {
                            "text": {"literalString": "DEVICE: RTR-CAN-ATLANTIC-01"},
                            "variant": "body",
                            "usageHint": "body1",
                            "style": {"color": "#00FFFF"},
                        }
                    },
                },
                {
                    "id": "info-row-2",
                    "component": {
                        "Text": {
                            "text": {
                                "literalString": "UPTIME: 195s STATE: OPERATIONAL"
                            },
                            "variant": "body",
                            "usageHint": "body1",
                            "style": {"color": "#32CD32"},
                        }
                    },
                },
                {"id": "divider-2", "component": {"Divider": {"axis": "horizontal"}}},
                {
                    "id": "status-bar",
                    "component": {
                        "Row": {
                            "children": {
                                "explicitList": [
                                    "indicator-pwr",
                                    "indicator-onli",
                                    "indicator-upst",
                                    "indicator-lan1",
                                ]
                            },
                            "style": {
                                "backgroundColor": "#070C14",
                                "padding": "4px",
                                "borderRadius": "8px",
                            },
                            "justify": "spaceAround",
                            "align": "center",
                        }
                    },
                },
                {
                    "id": "indicator-pwr",
                    "component": {
                        "Text": {
                            "text": {"literalString": "PWR"},
                            "variant": "caption",
                            "usageHint": "caption",
                            "style": {"color": "#00FF00"},
                        }
                    },
                },
                {
                    "id": "indicator-onli",
                    "component": {
                        "Text": {
                            "text": {"literalString": "ONLI"},
                            "variant": "caption",
                            "usageHint": "caption",
                            "style": {"color": "#00FF00"},
                        }
                    },
                },
                {
                    "id": "indicator-upst",
                    "component": {
                        "Text": {
                            "text": {"literalString": "UPST"},
                            "variant": "caption",
                            "usageHint": "caption",
                            "style": {"color": "#00FF00"},
                        }
                    },
                },
                {
                    "id": "indicator-lan1",
                    "component": {
                        "Text": {
                            "text": {"literalString": "LAN1"},
                            "variant": "caption",
                            "usageHint": "caption",
                            "style": {"color": "#00FF00"},
                        }
                    },
                },
            ],
        }
    },
]

# ============================================================================
# 2. Known-Working MCP Server Payload (Verified in router-mcp-server)
# ============================================================================
WORKING_MCP_V08_PAYLOAD = [
    {
        "beginRendering": {
            "surfaceId": "router-card-rtr_can_atlantic_01",
            "root": "card-root",
        }
    },
    {
        "surfaceUpdate": {
            "surfaceId": "router-card-rtr_can_atlantic_01",
            "components": [
                {"id": "card-root", "component": {"Card": {"child": "main-col"}}},
                {
                    "id": "main-col",
                    "component": {
                        "Column": {
                            "children": {
                                "explicitList": [
                                    "hdr-row",
                                    "sub-hdr",
                                    "telemetry-box",
                                    "led-box",
                                    "btn-row",
                                ]
                            }
                        }
                    },
                },
                {
                    "id": "hdr-row",
                    "component": {
                        "Row": {
                            "children": {"explicitList": ["title-text", "badge-text"]}
                        }
                    },
                },
                {
                    "id": "title-text",
                    "component": {
                        "Text": {
                            "usageHint": "h2",
                            "text": {"literalString": "RTR-CAN-ATLANTIC-01"},
                        }
                    },
                },
                {
                    "id": "badge-text",
                    "component": {
                        "Text": {
                            "usageHint": "caption",
                            "text": {"literalString": " [OPERATIONAL]"},
                        }
                    },
                },
                {
                    "id": "sub-hdr",
                    "component": {
                        "Text": {
                            "usageHint": "body2",
                            "text": {
                                "literalString": "ID: RTR-CAN-ATLANTIC-01 • Location: Halifax NS"
                            },
                        }
                    },
                },
                {
                    "id": "telemetry-box",
                    "component": {
                        "Column": {
                            "children": {
                                "explicitList": ["t-line-1", "t-line-2", "t-line-3"]
                            }
                        }
                    },
                },
                {
                    "id": "t-line-1",
                    "component": {
                        "Text": {
                            "usageHint": "monospace",
                            "text": {
                                "literalString": "UPTIME: 195s | STATE: OPERATIONAL"
                            },
                        }
                    },
                },
                {
                    "id": "t-line-2",
                    "component": {
                        "Text": {
                            "usageHint": "monospace",
                            "text": {
                                "literalString": "MFG/MODEL: Cisco Systems C8500-12X4QC"
                            },
                        }
                    },
                },
                {
                    "id": "t-line-3",
                    "component": {
                        "Text": {
                            "usageHint": "monospace",
                            "text": {
                                "literalString": "DEPLOYED: Jul 14, 03:43:49 PM | REV: 00012-78k"
                            },
                        }
                    },
                },
                {
                    "id": "led-box",
                    "component": {
                        "Text": {
                            "usageHint": "body1",
                            "text": {
                                "literalString": "LED Status: PWR:🟢  ONLINE:🟢  UPSTREAM:🟢  LAN1:🟢  LAN2:🟢  LAN3:⚫  LAN4:⚫  SEND:⚫  RECV:⚫"
                            },
                        }
                    },
                },
                {
                    "id": "btn-row",
                    "component": {
                        "Row": {
                            "children": {
                                "explicitList": ["btn-pwr", "btn-rst", "btn-bgp"]
                            }
                        }
                    },
                },
                {
                    "id": "btn-pwr",
                    "component": {
                        "Button": {
                            "child": "btn-pwr-lbl",
                            "action": {
                                "name": "send_router_command",
                                "parameters": {
                                    "router_id": "RTR-CAN-ATLANTIC-01",
                                    "action": "POWER_TOGGLE",
                                },
                            },
                        }
                    },
                },
                {
                    "id": "btn-pwr-lbl",
                    "component": {"Text": {"text": {"literalString": "Toggle Power"}}},
                },
                {
                    "id": "btn-rst",
                    "component": {
                        "Button": {
                            "child": "btn-rst-lbl",
                            "action": {
                                "name": "send_router_command",
                                "parameters": {
                                    "router_id": "RTR-CAN-ATLANTIC-01",
                                    "action": "REBOOT",
                                },
                            },
                        }
                    },
                },
                {
                    "id": "btn-rst-lbl",
                    "component": {"Text": {"text": {"literalString": "Reboot System"}}},
                },
                {
                    "id": "btn-bgp",
                    "component": {
                        "Button": {
                            "child": "btn-bgp-lbl",
                            "action": {
                                "name": "send_router_command",
                                "parameters": {
                                    "router_id": "RTR-CAN-ATLANTIC-01",
                                    "action": "BGP_RESET",
                                },
                            },
                        }
                    },
                },
                {
                    "id": "btn-bgp-lbl",
                    "component": {
                        "Text": {"text": {"literalString": "Reset BGP Session"}}
                    },
                },
            ],
        }
    },
]

# ============================================================================
# 3. Converted Composer v0.9 Payload
# ============================================================================
CONVERTED_COMPOSER_V08_PAYLOAD = [
    {"beginRendering": {"surfaceId": "router-card-mock-composer", "root": "card-root"}},
    {
        "surfaceUpdate": {
            "surfaceId": "router-card-mock-composer",
            "components": [
                {
                    "id": "card-root",
                    "component": {
                        "Card": {
                            "child": "main-column",
                            "style": {
                                "backgroundColor": "#0B131E",
                                "borderRadius": "12px",
                            },
                        }
                    },
                },
                {
                    "id": "main-column",
                    "component": {
                        "Column": {
                            "children": {
                                "explicitList": [
                                    "header-row",
                                    "divider-1",
                                    "info-row-1",
                                    "info-row-2",
                                    "info-row-3",
                                    "info-row-4",
                                    "divider-2",
                                    "status-bar",
                                    "divider-3",
                                    "btn-row",
                                ]
                            },
                            "align": "stretch",
                        }
                    },
                },
                {
                    "id": "header-row",
                    "component": {
                        "Row": {
                            "children": {
                                "explicitList": ["header-icon", "header-texts"]
                            },
                            "align": "center",
                        }
                    },
                },
                {
                    "id": "header-icon",
                    "component": {
                        "Text": {"text": {"literalString": "🌐"}, "usageHint": "h2"}
                    },
                },
                {
                    "id": "header-texts",
                    "component": {
                        "Column": {
                            "children": {
                                "explicitList": [
                                    "header-title",
                                    "header-subtitle",
                                    "header-location",
                                ]
                            }
                        }
                    },
                },
                {
                    "id": "header-title",
                    "component": {
                        "Text": {
                            "text": {"literalString": "RTR-CAN-ATLANTIC-01"},
                            "usageHint": "h3",
                            "style": {"color": "#00B0FF"},
                        }
                    },
                },
                {
                    "id": "header-subtitle",
                    "component": {
                        "Text": {
                            "text": {"literalString": "Atlantic Hub Gateway Node"},
                            "usageHint": "caption",
                            "style": {"color": "#00B0FF"},
                        }
                    },
                },
                {
                    "id": "header-location",
                    "component": {
                        "Text": {
                            "text": {"literalString": "Halifax NS"},
                            "usageHint": "caption",
                            "style": {"color": "#00B0FF"},
                        }
                    },
                },
                {"id": "divider-1", "component": {"Divider": {"axis": "horizontal"}}},
                {
                    "id": "info-row-1",
                    "component": {
                        "Text": {
                            "text": {"literalString": "DEVICE: RTR-CAN-ATLANTIC-01"},
                            "usageHint": "body1",
                            "style": {"color": "#00FFFF"},
                        }
                    },
                },
                {
                    "id": "info-row-2",
                    "component": {
                        "Text": {
                            "text": {
                                "literalString": "UPTIME: 195s STATE: OPERATIONAL"
                            },
                            "usageHint": "body1",
                            "style": {"color": "#32CD32"},
                        }
                    },
                },
                {
                    "id": "info-row-3",
                    "component": {
                        "Text": {
                            "text": {
                                "literalString": "MFG/MODEL: CISCO-NEXUS-9000-X v4.18.2-LTS UPDATED: 03:43:08 PM"
                            },
                            "usageHint": "body1",
                            "style": {"color": "#00FFFF"},
                        }
                    },
                },
                {
                    "id": "info-row-4",
                    "component": {
                        "Text": {
                            "text": {
                                "literalString": "DEPLOYED: Jul 15, 10:56:59 AM REV: 00018-vdg"
                            },
                            "usageHint": "body1",
                            "style": {"color": "#32CD32"},
                        }
                    },
                },
                {"id": "divider-2", "component": {"Divider": {"axis": "horizontal"}}},
                {
                    "id": "status-bar",
                    "component": {
                        "Row": {
                            "children": {
                                "explicitList": [
                                    "indicator-pwr",
                                    "indicator-onli",
                                    "indicator-upst",
                                    "indicator-lan1",
                                    "indicator-lan2",
                                    "indicator-lan3",
                                    "indicator-lan4",
                                ]
                            },
                            "style": {
                                "backgroundColor": "#070C14",
                                "padding": "4px",
                                "borderRadius": "8px",
                            },
                            "justify": "spaceAround",
                            "align": "center",
                        }
                    },
                },
                {
                    "id": "indicator-pwr",
                    "component": {
                        "Text": {
                            "text": {"literalString": "PWR"},
                            "usageHint": "caption",
                            "style": {"color": "#00FF00"},
                        }
                    },
                },
                {"id": "divider-3", "component": {"Divider": {"axis": "horizontal"}}},
                {
                    "id": "btn-row",
                    "component": {"Row": {"children": {"explicitList": ["btn-pwr"]}}},
                },
                {
                    "id": "btn-pwr-text",
                    "component": {
                        "Text": {
                            "text": {"literalString": "PWR"},
                            "usageHint": "caption",
                            "style": {"color": "#00FF00"},
                        }
                    },
                },
                {
                    "id": "btn-pwr",
                    "component": {
                        "Button": {
                            "child": "btn-pwr-text",
                            "action": {
                                "name": "send_router_command",
                                "parameters": {
                                    "router_id": "RTR-CAN-ATLANTIC-01",
                                    "action": "POWER_TOGGLE",
                                },
                            },
                        }
                    },
                },
                {
                    "id": "indicator-onli",
                    "component": {
                        "Text": {
                            "text": {"literalString": "ONLI"},
                            "usageHint": "caption",
                            "style": {"color": "#00FF00"},
                        }
                    },
                },
                {
                    "id": "indicator-upst",
                    "component": {
                        "Text": {
                            "text": {"literalString": "UPST"},
                            "usageHint": "caption",
                            "style": {"color": "#00FF00"},
                        }
                    },
                },
                {
                    "id": "indicator-lan1",
                    "component": {
                        "Text": {
                            "text": {"literalString": "LAN1"},
                            "usageHint": "caption",
                            "style": {"color": "#00FF00"},
                        }
                    },
                },
                {
                    "id": "indicator-lan2",
                    "component": {
                        "Text": {
                            "text": {"literalString": "LAN2"},
                            "usageHint": "caption",
                            "style": {"color": "#00FF00"},
                        }
                    },
                },
                {
                    "id": "indicator-lan3",
                    "component": {
                        "Text": {
                            "text": {"literalString": "LAN3"},
                            "usageHint": "caption",
                            "style": {"color": "#808080"},
                        }
                    },
                },
                {
                    "id": "indicator-lan4",
                    "component": {
                        "Text": {
                            "text": {"literalString": "LAN4"},
                            "usageHint": "caption",
                            "style": {"color": "#808080"},
                        }
                    },
                },
                {
                    "id": "indicator-send",
                    "component": {
                        "Text": {
                            "text": {"literalString": "SEND"},
                            "usageHint": "caption",
                            "style": {"color": "#808080"},
                        }
                    },
                },
                {
                    "id": "indicator-recv",
                    "component": {
                        "Text": {
                            "text": {"literalString": "RECV"},
                            "usageHint": "caption",
                            "style": {"color": "#808080"},
                        }
                    },
                },
            ],
        }
    },
]


def transform_composer_json_to_adk_v08(
    composer_data: dict, surface_id: str = "router-card-mock-composer"
) -> list:
    """Transforms raw A2UI Composer v0.9 layout dict into ADK v0.8 Operations Array format.

    Args:
        composer_data: Raw JSON dict loaded from Composer export.
        surface_id: Targeted ADK surface ID.

    Returns:
        ADK v0.8 Operations Array structure.
    """
    raw_root = composer_data.get("root", "root")
    root_id = "card-root" if raw_root == "root" else raw_root
    raw_components = composer_data.get("components", [])

    # Pre-pass: Index children lists and button component IDs
    child_map = {}
    btn_ids = []
    for comp in raw_components:
        c_id = comp["id"]
        c_type = comp.get("component")
        if "children" in comp and isinstance(comp["children"], list):
            child_map[c_id] = comp["children"]
        if c_type == "Button":
            btn_ids.append(c_id)

    v08_components = []

    for comp in raw_components:
        comp_id = comp["id"]
        if comp_id == "info-panel":
            continue

        if comp_id == "root":
            comp_id = "card-root"

        comp_type = comp["component"]
        props = {}

        # Handle Icon fallback to Text
        if comp_type == "Icon":
            comp_type = "Text"
            props["text"] = {"literalString": "🌐"}
            props["usageHint"] = "h2"
        elif comp_id.startswith("indicator-") and comp_type == "Text":
            raw_text = str(comp.get("text", "")).strip()
            style = comp.get("style", {})
            color_val = str(style.get("color", "")).lower()

            if color_val in ("#00ff00", "#32cd32", "green"):
                indicator_symbol = "🟢"
            elif color_val in ("#ffcc00", "#ff9900", "amber", "yellow", "orange"):
                indicator_symbol = "🟠"
            elif color_val in ("#ff3333", "#ff0000", "red"):
                indicator_symbol = "🔴"
            else:
                indicator_symbol = "⚫"

            props["text"] = {"literalString": f"{indicator_symbol} {raw_text}"}
            props["usageHint"] = "caption"
            if color_val:
                props["style"] = {
                    "color": color_val if color_val != "#808080" else "#A0A0A0"
                }
        else:
            for k, v in comp.items():
                if k in ("id", "component"):
                    continue
                if k == "child":
                    props["child"] = "card-root" if v == "root" else v
                elif k == "children" and isinstance(v, list):
                    explicit_children = []
                    for child_id in v:
                        if child_id == "info-panel" and "info-panel" in child_map:
                            explicit_children.extend(child_map["info-panel"])
                        elif child_id in btn_ids:
                            continue
                        else:
                            explicit_children.append(
                                "card-root" if child_id == "root" else child_id
                            )

                    if comp_id == "main-column" and btn_ids:
                        if "divider-3" not in explicit_children:
                            explicit_children.append("divider-3")
                        if "btn-row" not in explicit_children:
                            explicit_children.append("btn-row")

                    props["children"] = {"explicitList": explicit_children}
                elif k == "text" and isinstance(v, str):
                    props["text"] = {"literalString": v}
                elif k == "variant":
                    props["variant"] = v
                    props["usageHint"] = "body" if v in ("body", "body1") else v
                elif k == "style" and isinstance(v, dict):
                    clean_style = {}
                    for sk, sv in v.items():
                        if sk in (
                            "color",
                            "backgroundColor",
                            "borderColor",
                            "borderWidth",
                            "borderStyle",
                            "padding",
                            "borderRadius",
                        ):
                            if sk == "color":
                                clean_style[sk] = (
                                    "#00FFFF" if not str(sv).strip() else sv
                                )
                            else:
                                clean_style[sk] = sv
                    if clean_style:
                        props["style"] = clean_style
                elif k == "action" and isinstance(v, dict):
                    props["action"] = {
                        "name": "send_router_command",
                        "parameters": {
                            "router_id": "RTR-CAN-ATLANTIC-01",
                            "action": "POWER_TOGGLE",
                        },
                    }
                else:
                    props[k] = v

        v08_components.append({"id": comp_id, "component": {comp_type: props}})

    if btn_ids:
        v08_components.append(
            {"id": "divider-3", "component": {"Divider": {"axis": "horizontal"}}}
        )
        v08_components.append(
            {
                "id": "btn-row",
                "component": {
                    "Row": {
                        "children": {"explicitList": btn_ids},
                        "style": {
                            "backgroundColor": "#070C14",
                            "padding": "6px",
                            "borderRadius": "8px",
                        },
                        "justify": "center",
                        "align": "center",
                    }
                },
            }
        )

    return [
        {"beginRendering": {"surfaceId": surface_id, "root": root_id}},
        {"surfaceUpdate": {"surfaceId": surface_id, "components": v08_components}},
    ]


def mock_render_test_card() -> str:
    """Returns the known-working A2UI v0.8 card wrapped inside <a2ui-json> tags.

    Returns:
        String containing <a2ui-json> enclosed payload.
    """
    return (
        f"<a2ui-json>\n{json.dumps(WORKING_V08_A2UI_PAYLOAD, indent=2)}\n</a2ui-json>"
    )


def mock_render_mcp_card() -> str:
    """Returns the working MCP server A2UI card payload wrapped inside <a2ui-json> tags.

    Returns:
        String containing <a2ui-json> enclosed payload.
    """
    return f"<a2ui-json>\n{json.dumps(WORKING_MCP_V08_PAYLOAD, indent=2)}\n</a2ui-json>"


def mock_render_converted_composer_card() -> str:
    """Reads a2ui-legacy.json directly and returns <a2ui-json> block after variable formatting.

    Returns:
        String containing <a2ui-json> enclosed payload.
    """
    import os
    from string import Template

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    paths_to_check = [
        os.path.join(base_dir, "app", "a2ui-legacy.json"),
        os.path.join(base_dir, "a2ui-legacy.json"),
    ]

    default_values = {
        "display_name": "RTR-CAN-ATLANTIC-01",
        "router_id": "RTR-CAN-ATLANTIC-01",
        "subtitle": "Atlantic Hub Gateway Node",
        "location": "Halifax NS",
        "uptime": "195s",
        "state": "OPERATIONAL",
        "mfg_model": "CISCO-NEXUS-9000-X v4.18.2-LTS UPDATED: 03:43:08 PM",
    }

    for json_path in paths_to_check:
        if os.path.exists(json_path):
            try:
                with open(json_path, encoding="utf-8") as f:
                    template_str = f.read()

                rendered_json_str = Template(template_str).safe_substitute(
                    default_values
                )
                v08_payload = json.loads(rendered_json_str)
                return f"<a2ui-json>\n{json.dumps(v08_payload, indent=2)}\n</a2ui-json>"
            except Exception as e:
                logger.warning(
                    f"Failed to load static a2ui-legacy.json at {json_path}: {e}"
                )

    # Fallback to in-memory payload if file read fails
    return f"<a2ui-json>\n{json.dumps(CONVERTED_COMPOSER_V08_PAYLOAD, indent=2)}\n</a2ui-json>"
