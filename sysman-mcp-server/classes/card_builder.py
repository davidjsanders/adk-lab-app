"""A2UI Card builder for formatting system telemetry into interactive components."""

from typing import Any, Dict, List

from models import SystemStatus
from helpers import (
    generate_donut_chart,
    generate_horizontal_bar,
    generate_range_gauge,
    generate_status_pill,
    generate_material_icon_svg,
    generate_number_widget,
    generate_traffic_light_svg,
)


class CardBuilder:
    """Constructs layout and telemetry components for interactive A2UI status cards."""

    def __init__(self, system_status: SystemStatus, surface_id: str) -> None:
        """Initializes the builder with system status and surface context.

        Args:
            system_status: SystemStatus model containing telemetry data.
            surface_id: Unique string surface identifier for the card rendering session.
        """
        self.status = system_status
        self.surface_id = surface_id

    def build(self) -> List[Dict[str, Any]]:
        """Assembles and returns list of A2UI components representing the system.

        Returns:
            List of dictionary components compliant with A2UI v0.8 specification.
        """
        system_id = self.status.system_id
        sys_type = self.status.type
        name = self.status.name
        status = self.status.status
        description = self.status.description
        uptime = self.status.uptime_seconds
        icon_name = self.status.default_icon

        # Format Uptime
        d = uptime // 86400
        h = (uptime % 86400) // 3600
        m = (uptime % 3600) // 60
        s = uptime % 60
        uptime_str = f"{d}d {h}h {m}m {s}s"

        # Resolve status colors
        status_color = "#22C55E"
        if status == "DEGRADED":
            status_color = "#F59E0B"
        elif status in ("UNHEALTHY", "REBOOTING", "UNKNOWN"):
            status_color = "#EF4444"

        type_labels = {
            "jira": "JIRA APP",
            "confluence": "CONFLUENCE APP",
            "linux": "LINUX VM",
        }

        # Generate SVGs
        header_icon_uri = generate_material_icon_svg(icon_name, "#38BDF8")
        traffic_light_uri = generate_traffic_light_svg(status)

        components = [
            # 1. Main Card Root
            {
                "id": "card-root",
                "component": {
                    "Card": {
                        "child": "main-column",
                        "style": {
                            "backgroundColor": "#0B131E",
                            "borderRadius": "12px",
                            "padding": "12px",
                        },
                    }
                },
            },
            # 2. Main Column Wrapper
            {
                "id": "main-column",
                "component": {
                    "Column": {
                        "children": {
                            "explicitList": [
                                "header-row",
                                "divider-1",
                                "description-text",
                                "details-row",
                                "divider-2",
                                "metrics-title-text",
                                "metrics-column",
                                "divider-3",
                                "actions-row",
                            ]
                        },
                        "align": "stretch",
                    }
                },
                "style": {"margin": "0px", "padding": "0px", "gap": "6px"},
            },
            # 3. Header row
            {
                "id": "header-row",
                "component": {
                    "Row": {
                        "children": {
                            "explicitList": [
                                "header-icon",
                                "header-text",
                                "header-status-group",
                            ]
                        },
                        "justify": "spaceBetween",
                        "align": "center",
                    }
                },
            },
            {
                "id": "header-icon",
                "component": {
                    "Image": {"url": {"literalString": header_icon_uri}, "fit": "contain"}
                },
                "style": {"width": "28px", "height": "28px"},
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
                "style": {"fillWidth": True, "paddingLeft": "8px"},
            },
            {
                "id": "header-name",
                "component": {
                    "Text": {
                        "text": {"literalString": name},
                        "usageHint": "h3",
                        "style": {"color": "#FFFFFF", "fontWeight": "700"},
                    }
                },
            },
            {
                "id": "header-id",
                "component": {
                    "Text": {
                        "text": {
                            "literalString": f"ID: {system_id} | Type: {type_labels.get(sys_type, 'SYSTEM')}"
                        },
                        "usageHint": "caption",
                        "style": {"color": "#38BDF8"},
                    }
                },
            },
            {
                "id": "header-status-group",
                "component": {
                    "Row": {
                        "children": {
                            "explicitList": [
                                "header-status-light",
                                "header-status-text",
                            ]
                        },
                        "align": "center",
                    }
                },
                "style": {"gap": "6px", "width": "110px", "flexShrink": 0},
            },
            {
                "id": "header-status-light",
                "component": {
                    "Image": {"url": {"literalString": traffic_light_uri}, "fit": "contain"}
                },
                "style": {"width": "14px", "height": "36px"},
            },
            {
                "id": "header-status-text",
                "component": {"Text": {"text": {"literalString": status}, "usageHint": "body1"}},
                "style": {"color": status_color, "fontWeight": "bold"},
            },
            {"id": "divider-1", "component": {"Divider": {"axis": "horizontal"}}},
            
            # 4. Service Description
            {
                "id": "description-text",
                "component": {
                    "Text": {
                        "text": {"literalString": description},
                        "usageHint": "body",
                        "style": {
                            "color": "#94A3B8",  # slate-400
                            "fontStyle": "italic",
                        },
                    }
                },
            },
            
            # 5. Uptime Details row (placed in description section without divider separator)
            {
                "id": "details-row",
                "component": {
                    "Row": {
                        "children": {"explicitList": ["details-uptime-lbl", "details-uptime-val"]},
                        "justify": "spaceBetween",
                    }
                },
            },
            {
                "id": "details-uptime-lbl",
                "component": {
                    "Text": {
                        "text": {"literalString": "System Uptime: "},
                        "usageHint": "body",
                        "style": {"color": "#94A3B8"},
                    }
                },
            },
            {
                "id": "details-uptime-val",
                "component": {
                    "Text": {
                        "text": {"literalString": uptime_str},
                        "usageHint": "body",
                        "style": {"color": "#32CD32"},
                    }
                },
            },
            {"id": "divider-2", "component": {"Divider": {"axis": "horizontal"}}},
            
            # 6. Metrics Header & Grid
            {
                "id": "metrics-title-text",
                "component": {
                    "Text": {
                        "text": {"literalString": "System Telemetry Metrics"},
                        "usageHint": "body",
                        "style": {"color": "#FFFFFF", "fontWeight": "bold"},
                    }
                },
            },
            # Metrics container column
            {
                "id": "metrics-column",
                "component": {"Column": {"children": {"explicitList": []}, "align": "stretch"}},
                "style": {"gap": "6px"},
            },
            {"id": "divider-3", "component": {"Divider": {"axis": "horizontal"}}},
            
            # 7. Actions row container (moved to bottom of card layout)
            {
                "id": "actions-row",
                "component": {
                    "Row": {"children": {"explicitList": []}, "justify": "spaceAround"}
                },
            },
        ]

        # Dynamic metrics content generation
        metrics_children_ids = []
        for m_spec in self.status.metrics:
            m_id = m_spec.id
            m_type = m_spec.type
            label = m_spec.label
            value = m_spec.value or 0.0
            val_text = m_spec.val_text or str(value)

            if m_type == "donut_chart":
                svg_data_uri = generate_donut_chart(value, label)
                components.append(
                    {
                        "id": m_id,
                        "component": {
                            "Image": {"url": {"literalString": svg_data_uri}, "fit": "contain"}
                        },
                    }
                )
                metrics_children_ids.append(m_id)

            elif m_type == "progress_bar":
                svg_data_uri = generate_horizontal_bar(value, label, val_text)
                components.append(
                    {
                        "id": m_id,
                        "component": {
                            "Image": {"url": {"literalString": svg_data_uri}, "fit": "contain"}
                        },
                    }
                )
                metrics_children_ids.append(m_id)

            elif m_type == "range_gauge":
                max_value = m_spec.max_value or 100.0
                yellow_threshold = m_spec.yellow_threshold or 50.0
                red_threshold = m_spec.red_threshold or 80.0
                svg_data_uri = generate_range_gauge(
                    value, max_value, label, val_text, yellow_threshold, red_threshold
                )
                components.append(
                    {
                        "id": m_id,
                        "component": {
                            "Image": {"url": {"literalString": svg_data_uri}, "fit": "contain"}
                        },
                    }
                )
                metrics_children_ids.append(m_id)

            elif m_type == "status_pill":
                pill_status = m_spec.status or "healthy"
                svg_data_uri = generate_status_pill(label, val_text, pill_status)
                components.append(
                    {
                        "id": m_id,
                        "component": {
                            "Image": {"url": {"literalString": svg_data_uri}, "fit": "contain"}
                        },
                    }
                )
                metrics_children_ids.append(m_id)

            elif m_type == "number":
                svg_data_uri = generate_number_widget(label, val_text)
                components.append(
                    {
                        "id": m_id,
                        "component": {
                            "Image": {"url": {"literalString": svg_data_uri}, "fit": "contain"}
                        },
                    }
                )
                metrics_children_ids.append(m_id)

            else:
                fallback_txt_id = f"{m_id}-fallback-txt"
                components.append(
                    {
                        "id": fallback_txt_id,
                        "component": {
                            "Text": {
                                "text": {"literalString": f"{label}: {val_text}"},
                                "usageHint": "body",
                                "style": {"color": "#E2E8F0"},
                            }
                        },
                    }
                )
                metrics_children_ids.append(fallback_txt_id)

        # Lay out metrics in a 4-column grid (up to 4 per row)
        grid_rows_ids = []
        for i in range(0, len(metrics_children_ids), 4):
            row_id = f"metrics-row-{i//4}"
            row_children = metrics_children_ids[i : i + 4]
            components.append(
                {
                    "id": row_id,
                    "component": {
                        "Row": {
                            "children": {"explicitList": row_children},
                            "justify": "spaceBetween",
                            "align": "center",
                        }
                    },
                    "style": {"fillWidth": True, "gap": "8px"},
                }
            )
            grid_rows_ids.append(row_id)

        # Bind grid rows to metrics-column Column children
        for comp in components:
            if comp["id"] == "metrics-column":
                comp["component"]["Column"]["children"]["explicitList"] = grid_rows_ids

        # Generate action buttons dynamically
        actions_children_ids = []
        for a_spec in self.status.actions:
            a_id = a_spec.id
            label = a_spec.label
            command = a_spec.command
            color = a_spec.color or "#00FF00"
            components.extend(
                [
                    {
                        "id": f"{a_id}-txt",
                        "component": {
                            "Text": {
                                "text": {"literalString": label},
                                "usageHint": "caption",
                                "style": {"color": color},
                            }
                        },
                    },
                    {
                        "id": a_id,
                        "component": {
                            "Button": {
                                "child": f"{a_id}-txt",
                                "action": {
                                    "name": "execute_system_command",
                                    "parameters": {"system_id": system_id, "command": command},
                                },
                            }
                        },
                    },
                ]
            )
            actions_children_ids.append(a_id)

        # Bind actions-row children
        for comp in components:
            if comp["id"] == "actions-row":
                comp["component"]["Row"]["children"]["explicitList"] = actions_children_ids

        return components

    def build_logs_card(self) -> List[Dict[str, Any]]:
        """Assembles and returns list of A2UI components representing a dedicated logs viewer.

        Returns:
            List of dictionary components compliant with A2UI v0.8 specification.
        """
        system_id = self.status.system_id
        name = self.status.name
        status = self.status.status
        icon_name = "history"

        # Resolve status colors
        status_color = "#22C55E"
        if status == "DEGRADED":
            status_color = "#F59E0B"
        elif status in ("UNHEALTHY", "REBOOTING", "UNKNOWN"):
            status_color = "#EF4444"

        # Generate SVGs
        header_icon_uri = generate_material_icon_svg(icon_name, "#38BDF8")
        traffic_light_uri = generate_traffic_light_svg(status)

        components = [
            # 1. Logs Card Root
            {
                "id": "logs-card-root",
                "component": {
                    "Card": {
                        "child": "logs-main-column",
                        "style": {
                            "backgroundColor": "#0B131E",
                            "borderRadius": "12px",
                            "padding": "12px",
                        },
                    }
                },
            },
            # 2. Main Column Wrapper
            {
                "id": "logs-main-column",
                "component": {
                    "Column": {
                        "children": {
                            "explicitList": [
                                "logs-header-row",
                                "logs-divider-1",
                                "logs-title-text",
                                "logs-console",
                            ]
                        },
                        "align": "stretch",
                    }
                },
                "style": {"margin": "0px", "padding": "0px", "gap": "6px"},
            },
            # 3. Header row
            {
                "id": "logs-header-row",
                "component": {
                    "Row": {
                        "children": {
                            "explicitList": [
                                "logs-header-icon",
                                "logs-header-text",
                                "logs-header-status-group",
                            ]
                        },
                        "justify": "spaceBetween",
                        "align": "center",
                    }
                },
            },
            {
                "id": "logs-header-icon",
                "component": {
                    "Image": {"url": {"literalString": header_icon_uri}, "fit": "contain"}
                },
                "style": {"width": "28px", "height": "28px"},
            },
            {
                "id": "logs-header-text",
                "component": {
                    "Column": {
                        "children": {
                            "explicitList": ["logs-header-name", "logs-header-id"]
                        }
                    }
                },
                "style": {"fillWidth": True, "paddingLeft": "8px"},
            },
            {
                "id": "logs-header-name",
                "component": {
                    "Text": {
                        "text": {"literalString": f"{name} Diagnostics"},
                        "usageHint": "h3",
                        "style": {"color": "#FFFFFF", "fontWeight": "700"},
                    }
                },
            },
            {
                "id": "logs-header-id",
                "component": {
                    "Text": {
                        "text": {
                            "literalString": f"ID: {system_id} | Logs limit: 15"
                        },
                        "usageHint": "caption",
                        "style": {"color": "#38BDF8"},
                    }
                },
            },
            {
                "id": "logs-header-status-group",
                "component": {
                    "Row": {
                        "children": {
                            "explicitList": [
                                "logs-header-status-light",
                                "logs-header-status-text",
                            ]
                        },
                        "align": "center",
                    }
                },
                "style": {"gap": "6px", "width": "110px", "flexShrink": 0},
            },
            {
                "id": "logs-header-status-light",
                "component": {
                    "Image": {"url": {"literalString": traffic_light_uri}, "fit": "contain"}
                },
                "style": {"width": "14px", "height": "36px"},
            },
            {
                "id": "logs-header-status-text",
                "component": {"Text": {"text": {"literalString": status}, "usageHint": "body1"}},
                "style": {"color": status_color, "fontWeight": "bold"},
            },
            {"id": "logs-divider-1", "component": {"Divider": {"axis": "horizontal"}}},
            
            # 4. Logs Title & Console
            {
                "id": "logs-title-text",
                "component": {
                    "Text": {
                        "text": {"literalString": "System Diagnostics Log Stream"},
                        "usageHint": "body",
                        "style": {"color": "#FFFFFF", "fontWeight": "bold"},
                    }
                },
            },
        ]

        # Generate recent logs console content dynamically
        logs_children = []
        for index, log in enumerate(self.status.logs):
            log_id = f"log-line-{index}"
            level_str = f"[{log.level}]"
            log_text = f"{log.timestamp} {level_str:<9} {log.message}"

            # Style console output color
            color = "#86EFAC"  # default soft green for INFO
            if log.level == "WARNING":
                color = "#FDE68A"  # soft yellow
            elif log.level == "ERROR":
                color = "#FCA5A5"  # soft red
            elif log.level == "DEBUG":
                color = "#94A3B8"  # gray

            components.append(
                {
                    "id": log_id,
                    "component": {
                        "Text": {
                            "text": {"literalString": log_text},
                            "usageHint": "body",
                            "style": {
                                "color": color,
                                "fontFamily": "monospace",
                                "fontSize": "11px",
                            },
                        }
                    },
                }
            )
            logs_children.append(log_id)

        # Logs console component (350px for dedicated logs viewer)
        components.append(
            {
                "id": "logs-console",
                "component": {"Column": {"children": {"explicitList": logs_children}, "align": "stretch"}},
                "style": {
                    "backgroundColor": "#020617",  # deep console background slate-950
                    "borderRadius": "6px",
                    "padding": "8px",
                    "gap": "4px",
                    "height": "350px",  # Higher height limit for readability on dedicated cards
                    "overflowY": "auto",  # Enable scrollbar if logs exceed limit
                },
            }
        )

        return components
