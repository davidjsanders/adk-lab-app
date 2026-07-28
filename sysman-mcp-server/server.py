#!/usr/bin/env python3
"""SysMan Model Context Protocol (MCP) Server.

Provides FastMCP tools to query system statuses, retrieve logs,
execute configuration and lifecycle controls, and render interactive
A2UI cards for simulated Linux hosts, Jira app servers, and Confluence nodes.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from fastmcp import FastMCP
import requests

# Load environment configuration
load_dotenv()

# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sysman-mcp-server")

mcp = FastMCP("SysMan Operations MCP Server")

EMULATOR_URL = os.getenv("EMULATOR_URL", "http://127.0.0.1:8081").rstrip("/")
CONTROL_HEADER = os.getenv("CONTROL_HEADER", "X-Control-Password")
CONTROL_PASSWORD = os.getenv("CONTROL_PASSWORD", "SysManSecretPass123!")


def get_headers() -> Dict[str, str]:
    """Helper to compile headers for emulator request authentication.

    Returns:
        Dictionary of headers containing control authorization tokens.
    """
    return {
        "Content-Type": "application/json",
        CONTROL_HEADER: CONTROL_PASSWORD
    }


@mcp.tool()
def list_systems() -> List[Dict[str, Any]]:
    """Lists all registered virtual systems in the fleet.

    Returns:
        List of dictionaries containing system metadata (id, name, type, status).

    Raises:
        RuntimeError: If communicating with the emulator service fails.
    """
    url = f"{EMULATOR_URL}/api/status"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return data.get("systems", [])
    except Exception as err:
        logger.error(f"Failed querying active systems list: {err}")
        raise RuntimeError(f"Failed querying active systems from emulator at {url}: {err}")


@mcp.tool()
def get_system_status(system_id: str) -> Dict[str, Any]:
    """Queries detailed status, metrics, and health of a specific system.

    Args:
        system_id: Unique string ID of the target system (e.g. 'linux-server-01').

    Returns:
        Dictionary containing metadata, active metrics, health status, and recent logs.

    Raises:
        RuntimeError: If status query fails.
    """
    url = f"{EMULATOR_URL}/api/status"
    try:
        resp = requests.get(url, params={"system_id": system_id}, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as err:
        logger.error(f"Failed fetching status for system '{system_id}': {err}")
        raise RuntimeError(f"Failed fetching status for '{system_id}' at {url}: {err}")


@mcp.tool()
def execute_system_command(system_id: str, command: str) -> Dict[str, Any]:
    """Sends lifecycle restarts, Garbage Collection, websocket reconnects or fault injections.

    Args:
        system_id: Target system ID.
        command: Command keyword to execute.
          Valid values:
            - For Linux: 'REBOOT', 'STOP_NODE_EXPORTER', 'START_NODE_EXPORTER', 'INJECT_FAULT', 'CLEAR_FAULT'
            - For Jira: 'RESTART_JIRA', 'GC_CLEANUP', 'EXPAND_DB_POOL', 'EXHAUST_DB_POOL', 'TRIGGER_JVM_LEAK', 'RESET_SIMULATION'
            - For Confluence: 'REBOOT', 'RECONNECT_WEBSOCKETS', 'PURGE_ATTACHMENTS', 'DROP_WEBSOCKETS', 'FILL_DISK', 'RESET_SIMULATION'

    Returns:
        Dictionary containing execution result status and message.

    Raises:
        RuntimeError: If command execution request fails.
    """
    url = f"{EMULATOR_URL}/api/command"
    payload = {
        "system_id": system_id,
        "command": command
    }
    try:
        headers = get_headers()
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as err:
        logger.error(f"Failed executing command '{command}' on '{system_id}': {err}")
        raise RuntimeError(f"Failed executing command '{command}' on '{system_id}' at {url}: {err}")


@mcp.tool()
def get_system_logs(system_id: str, limit: int = 15) -> List[Dict[str, Any]]:
    """Retrieves recent syslog or application logs for the requested system.

    Args:
        system_id: Target system ID.
        limit: Number of recent log lines to retrieve (default: 15).

    Returns:
        List of syslog dictionaries containing level, timestamp and log message.

    Raises:
        RuntimeError: If log query fails.
    """
    url = f"{EMULATOR_URL}/api/logs"
    try:
        resp = requests.get(url, params={"system_id": system_id, "limit": limit}, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return data.get("logs", [])
    except Exception as err:
        logger.error(f"Failed querying logs for system '{system_id}': {err}")
        raise RuntimeError(f"Failed querying logs for '{system_id}' at {url}: {err}")


def _generate_donut_chart(percentage: float, label: str = "") -> str:
    """Generates a Base64-encoded SVG circular donut progress chart.

    Args:
        percentage: The progress percentage value (0.0 to 100.0).
        label: Text sub-label printed inside center of circle.

    Returns:
        Data URI string formatted as data:image/svg+xml;base64,...
    """
    import base64
    percentage = max(0.0, min(100.0, percentage))
    free = 100.0 - percentage

    label_len = len(label)
    font_size = 4.0 if label_len > 24 else (5.0 if label_len > 18 else 6.0)

    svg = f"""<svg width="100%" height="100%" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
  <rect x="2" y="2" width="76" height="76" rx="8" fill="#111827" stroke="#374151" stroke-width="1" />
  <circle cx="40" cy="44" r="18" fill="#0B131E" />
  <circle cx="40" cy="44" r="18" fill="transparent" stroke="#EF4444" stroke-width="4.5" />
  <circle cx="40" cy="44" r="18" fill="transparent" stroke="#22C55E" stroke-width="4.5" stroke-dasharray="{free * 1.13097} {percentage * 1.13097}" stroke-dashoffset="28.27" />
  <text x="40" y="15" font-family="sans-serif" font-size="{font_size}" fill="#94A3B8" text-anchor="middle" font-weight="bold">{label}</text>
  <text x="40" y="46.5" font-family="sans-serif" font-size="7" fill="#FFFFFF" text-anchor="middle" font-weight="bold">{percentage:.1f}%</text>
</svg>"""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def _generate_horizontal_bar(percentage: float, label: str, val_text: str) -> str:
    """Generates a Base64-encoded SVG horizontal progress bar.

    Args:
        percentage: The progress percentage value (0.0 to 100.0).
        label: Text label describing the progress bar.
        val_text: Raw display value text printed adjacent to the label.

    Returns:
        Data URI string formatted as data:image/svg+xml;base64,...
    """
    import base64
    percentage = max(0.0, min(100.0, percentage))
    fill_width = percentage * 0.6

    label_len = len(label)
    font_size = 4.0 if label_len > 24 else (5.0 if label_len > 18 else 6.0)

    svg = f"""<svg width="100%" height="100%" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
  <rect x="2" y="2" width="76" height="76" rx="8" fill="#111827" stroke="#374151" stroke-width="1" />
  <text x="40" y="18" font-family="sans-serif" font-size="{font_size}" fill="#94A3B8" text-anchor="middle" font-weight="bold">{label}</text>
  <rect x="10" y="34" width="60" height="7" rx="3.5" fill="#1F2937" />
  <rect x="10" y="34" width="{fill_width}" height="7" rx="3.5" fill="#38BDF8" />
  <text x="40" y="58" font-family="sans-serif" font-size="7.5" fill="#FFFFFF" text-anchor="middle" font-weight="bold">{val_text}</text>
</svg>"""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def _generate_range_gauge(value: float, max_value: float, label: str, val_text: str, yellow_threshold: float, red_threshold: float) -> str:
    """Generates a Base64-encoded SVG range gauge scale with a pointer indicator.

    Args:
        value: Current metric value.
        max_value: Target maximum bounds of the scale (maps to 100% width).
        label: Metric label description.
        val_text: Display value string.
        yellow_threshold: Yellow warning boundary metric value.
        red_threshold: Red critical boundary metric value.

    Returns:
        Data URI string formatted as data:image/svg+xml;base64,...
    """
    import base64
    percentage = (value / max_value) * 100.0 if max_value > 0 else 0.0
    percentage = max(0.0, min(100.0, percentage))

    yellow_pct = (yellow_threshold / max_value) * 100.0 if max_value > 0 else 50.0
    red_pct = (red_threshold / max_value) * 100.0 if max_value > 0 else 80.0

    ptr_x = 10 + (percentage * 0.6)

    label_len = len(label)
    font_size = 4.0 if label_len > 24 else (5.0 if label_len > 18 else 6.0)

    svg = f"""<svg width="100%" height="100%" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
  <rect x="2" y="2" width="76" height="76" rx="8" fill="#111827" stroke="#374151" stroke-width="1" />
  <text x="40" y="18" font-family="sans-serif" font-size="{font_size}" fill="#94A3B8" text-anchor="middle" font-weight="bold">{label}</text>
  
  <rect x="10" y="38" width="{yellow_pct * 0.6}" height="6" fill="#22C55E" rx="3" />
  <rect x="{10 + yellow_pct * 0.6}" y="38" width="{(red_pct - yellow_pct) * 0.6}" height="6" fill="#EAB308" />
  <rect x="{10 + red_pct * 0.6}" y="38" width="{(100 - red_pct) * 0.6}" height="6" fill="#EF4444" rx="3" />
  
  <polygon points="{ptr_x},36 {ptr_x - 3},30 {ptr_x + 3},30" fill="#FFFFFF" />
  <text x="40" y="58" font-family="sans-serif" font-size="7.5" fill="#FFFFFF" text-anchor="middle" font-weight="bold">{val_text}</text>
</svg>"""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def _generate_status_pill(label: str, val_text: str, status: str) -> str:
    """Generates a Base64-encoded SVG status banner pill with a custom icon.

    Args:
        label: Status metric label description.
        val_text: Formatted display text state.
        status: One of 'healthy', 'warning', or 'critical'.

    Returns:
        Data URI string formatted as data:image/svg+xml;base64,...
    """
    import base64
    if status == "healthy":
        border_color, text_color, bg_color = "#22C55E", "#86EFAC", "#064E3B"
        icon_path = "M5 13l4 4L19 7"
    elif status == "warning":
        border_color, text_color, bg_color = "#F59E0B", "#FDE68A", "#78350F"
        icon_path = "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
    else:  # critical or unknown
        border_color, text_color, bg_color = "#EF4444", "#FCA5A5", "#7F1D1D"
        icon_path = "M6 18L18 6M6 6l12 12"

    label_len = len(label)
    font_size = 4.0 if label_len > 24 else (5.0 if label_len > 18 else 6.0)

    svg = f"""<svg width="100%" height="100%" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
  <rect x="2" y="2" width="76" height="76" rx="8" fill="#111827" stroke="#374151" stroke-width="1" />
  <text x="40" y="18" font-family="sans-serif" font-size="{font_size}" fill="#94A3B8" text-anchor="middle" font-weight="bold">{label}</text>
  
  <rect x="25" y="28" width="30" height="30" rx="15" fill="{bg_color}" stroke="{border_color}" stroke-width="1" />
  <svg x="33" y="36" width="14" height="14" viewBox="0 0 24 24">
    <path d="{icon_path}" stroke="{text_color}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />
  </svg>
  
  <text x="40" y="68" font-family="sans-serif" font-size="7" fill="{text_color}" text-anchor="middle" font-weight="bold">{val_text}</text>
</svg>"""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def _build_card_components(system_id: str, surface_id: str) -> list:
    """Compiles the full list of layout and telemetry components for the card.

    Args:
        system_id: Unique string ID of target system.
        surface_id: Active rendering surface context window ID.

    Returns:
        List of A2UI component dictionaries.
    """
    import json

    # 1. Fetch data from emulator status endpoint
    sys = get_system_status(system_id)
    sys_type = sys.get("type", "linux")
    name = sys.get("name", system_id)
    status = sys.get("status", "UNKNOWN")
    uptime = sys.get("uptime_seconds", 0)

    # Format Uptime
    d = uptime // 86400
    h = (uptime % 86400) // 3600
    m = (uptime % 3600) // 60
    s = uptime % 60
    uptime_str = f"{d}d {h}h {m}m {s}s"

    # Resolve status colors
    status_color = "#22C55E"
    status_icon = "🟢"
    if status == "DEGRADED":
        status_color = "#F59E0B"
        status_icon = "🟠"
    elif status in ("UNHEALTHY", "REBOOTING", "UNKNOWN"):
        status_color = "#EF4444"
        status_icon = "🔴"

    header_icons = {
        "jira": "💼",
        "confluence": "💼",
        "linux": "💻"
    }
    type_labels = {
        "jira": "JIRA APP",
        "confluence": "CONFLUENCE APP",
        "linux": "LINUX VM"
    }

    # 2. Base layout structures (no tab container!)
    components = [
        {
            "id": "card-root",
            "component": {
                "Card": {
                    "child": "main-column",
                    "style": {
                        "backgroundColor": "#0B131E",
                        "borderRadius": "12px",
                        "padding": "12px"
                    }
                }
            }
        },
        {
            "id": "main-column",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": [
                            "header-row",
                            "divider-1",
                            "details-row",
                            "divider-2",
                            "metrics-column",
                            "divider-3",
                            "actions-row"
                        ]
                    },
                    "align": "stretch"
                }
            },
            "style": {
                "margin": "0px",
                "padding": "0px",
                "gap": "6px"
            }
        },
        # Header components
        {
            "id": "header-row",
            "component": {
                "Row": {
                    "children": {
                        "explicitList": ["header-icon", "header-text", "header-status-badge"]
                    },
                    "justify": "spaceBetween",
                    "align": "center"
                }
            }
        },
        {
            "id": "header-icon",
            "component": {
                "Text": {
                    "text": {"literalString": header_icons.get(sys_type, "💼")},
                    "usageHint": "h2"
                }
            }
        },
        {
            "id": "header-text",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": ["header-name", "header-id"]
                    }
                }
            },
            "style": {"fillWidth": True, "paddingLeft": "8px"}
        },
        {
            "id": "header-name",
            "component": {
                "Text": {
                    "text": {"literalString": name},
                    "usageHint": "h3",
                    "style": {"color": "#FFFFFF", "fontWeight": "700"}
                }
            }
        },
        {
            "id": "header-id",
            "component": {
                "Text": {
                    "text": {"literalString": f"ID: {system_id} | Type: {type_labels.get(sys_type, 'SYSTEM')}"},
                    "usageHint": "caption",
                    "style": {"color": "#38BDF8"}
                }
            }
        },
        {
            "id": "header-status-badge",
            "component": {
                "Text": {
                    "text": {"literalString": f"{status_icon} {status}"},
                    "usageHint": "body",
                    "style": {"color": status_color, "fontWeight": "700"}
                }
            }
        },
        {
            "id": "divider-1",
            "component": {"Divider": {"axis": "horizontal"}}
        },
        # Details row
        {
            "id": "details-row",
            "component": {
                "Row": {
                    "children": {
                        "explicitList": ["details-uptime-lbl", "details-uptime-val"]
                    },
                    "justify": "spaceBetween"
                }
            }
        },
        {
            "id": "details-uptime-lbl",
            "component": {
                "Text": {
                    "text": {"literalString": "System Uptime: "},
                    "usageHint": "body",
                    "style": {"color": "#94A3B8"}
                }
            }
        },
        {
            "id": "details-uptime-val",
            "component": {
                "Text": {
                    "text": {"literalString": uptime_str},
                    "usageHint": "body",
                    "style": {"color": "#32CD32"}
                }
            }
        },
        {
            "id": "divider-2",
            "component": {"Divider": {"axis": "horizontal"}}
        },
        # Metrics container column
        {
            "id": "metrics-column",
            "component": {
                "Column": {
                    "children": {
                        "explicitList": []
                    },
                    "align": "stretch"
                }
            },
            "style": {"gap": "6px"}
        },
        {
            "id": "divider-3",
            "component": {"Divider": {"axis": "horizontal"}}
        },
        # Actions row container
        {
            "id": "actions-row",
            "component": {
                "Row": {
                    "children": {
                        "explicitList": []
                    },
                    "justify": "spaceAround"
                }
            }
        }
    ]

    # 3. Dynamic content generation based on active metrics specification passed from emulator
    metrics_children_ids = []
    for m_spec in sys.get("metrics", []):
        m_id = m_spec["id"]
        m_type = m_spec["type"]
        label = m_spec["label"]
        value = m_spec.get("value", 0.0)
        val_text = m_spec.get("val_text", str(value))

        if m_type == "donut_chart":
            svg_data_uri = _generate_donut_chart(value, label)
            components.append({
                "id": m_id,
                "component": {"Image": {"url": {"literalString": svg_data_uri}, "fit": "contain"}}
            })
            metrics_children_ids.append(m_id)

        elif m_type == "progress_bar":
            svg_data_uri = _generate_horizontal_bar(value, label, val_text)
            components.append({
                "id": m_id,
                "component": {"Image": {"url": {"literalString": svg_data_uri}, "fit": "contain"}}
            })
            metrics_children_ids.append(m_id)

        elif m_type == "range_gauge":
            max_value = m_spec.get("max_value", 100.0)
            yellow_threshold = m_spec.get("yellow_threshold", 50.0)
            red_threshold = m_spec.get("red_threshold", 80.0)
            svg_data_uri = _generate_range_gauge(value, max_value, label, val_text, yellow_threshold, red_threshold)
            components.append({
                "id": m_id,
                "component": {"Image": {"url": {"literalString": svg_data_uri}, "fit": "contain"}}
            })
            metrics_children_ids.append(m_id)

        elif m_type == "status_pill":
            status = m_spec.get("status", "healthy")
            svg_data_uri = _generate_status_pill(label, val_text, status)
            components.append({
                "id": m_id,
                "component": {"Image": {"url": {"literalString": svg_data_uri}, "fit": "contain"}}
            })
            metrics_children_ids.append(m_id)

        else:
            # Fallback text representation if instrument component type is unrecognized
            fallback_txt_id = f"{m_id}-fallback-txt"
            components.append({
                "id": fallback_txt_id,
                "component": {
                    "Text": {
                        "text": {"literalString": f"{label}: {val_text}"},
                        "usageHint": "body",
                        "style": {"color": "#E2E8F0"}
                    }
                }
            })
            metrics_children_ids.append(fallback_txt_id)

    # Lay out metrics in a 4-column grid (up to 4 per row)
    grid_rows_ids = []
    for i in range(0, len(metrics_children_ids), 4):
        row_id = f"metrics-row-{i//4}"
        row_children = metrics_children_ids[i:i+4]
        components.append({
            "id": row_id,
            "component": {
                "Row": {
                    "children": {"explicitList": row_children},
                    "justify": "spaceBetween",
                    "align": "center"
                }
            },
            "style": {"fillWidth": True, "gap": "8px"}
        })
        grid_rows_ids.append(row_id)

    # Bind grid rows to metrics-column Column children
    for comp in components:
        if comp["id"] == "metrics-column":
            comp["component"]["Column"]["children"]["explicitList"] = grid_rows_ids

    # 4. Generate action buttons dynamically passed from emulator
    actions_children_ids = []
    for a_spec in sys.get("actions", []):
        a_id = a_spec["id"]
        label = a_spec["label"]
        command = a_spec["command"]
        color = a_spec.get("color", "#00FF00")
        components.extend([
            {
                "id": f"{a_id}-txt",
                "component": {"Text": {"text": {"literalString": label}, "usageHint": "caption", "style": {"color": color}}}
            },
            {
                "id": a_id,
                "component": {
                    "Button": {
                        "child": f"{a_id}-txt",
                        "action": {
                            "name": "execute_system_command",
                            "parameters": {"system_id": system_id, "command": command}
                        }
                    }
                }
            }
        ])
        actions_children_ids.append(a_id)

    # Bind actions-row children
    for comp in components:
        if comp["id"] == "actions-row":
            comp["component"]["Row"]["children"]["explicitList"] = actions_children_ids

    return components


@mcp.tool()
def render_system_card(system_id: str) -> str:
    """Renders a native A2UI v0.8 interactive status card for the target system.

    Args:
        system_id: Unique string ID of target system.

    Returns:
        A2UI v0.8 JSON declarative card payload string enclosed in <a2ui-json> tags.

    Raises:
        RuntimeError: If status query fails.
    """
    import json
    import time
    surface_id = f"sysman_card_{system_id.lower().replace('-', '_')}_{int(time.time()*1000)}"
    try:
        components = _build_card_components(system_id, surface_id)
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
                    "components": components
                }
            }
        ]
        return f"<a2ui-json>\n{json.dumps(payload, indent=2)}\n</a2ui-json>"
    except Exception as err:
        logger.error(f"Failed rendering system card: {err}")
        raise RuntimeError(f"Failed rendering system card for {system_id}") from err


@mcp.tool()
def switch_system_card_tab(system_id: str, surface_id: str, tab: str) -> str:
    """Switches the view tab of the target system interactive card.

    Args:
        system_id: Unique string ID of target system.
        surface_id: The surface ID of the rendering card to update.
        tab: Target tab name to display (one of 'metrics', 'logs', 'config').

    Returns:
        A2UI v0.8 JSON declarative card surfaceUpdate command.
    """
    raise NotImplementedError("Tabs are no longer supported for system cards.")

# Expose ASGI HTTP application instance for server execution
app = mcp.http_app(transport="streamable-http", stateless_http=True)


if __name__ == "__main__":
    import sys
    transport = "stdio" if "--stdio" in sys.argv else "streamable-http"
    try:
        if transport == "stdio":
            mcp.run(transport=transport)
        else:
            port = int(os.getenv("PORT", "8002"))
            mcp.run(transport=transport, host="127.0.0.1", port=port)
    except (KeyboardInterrupt, SystemExit):
        logger.info("FastMCP server shut down cleanly.")
