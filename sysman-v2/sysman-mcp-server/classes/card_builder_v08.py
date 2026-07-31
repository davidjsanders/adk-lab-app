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

"""A2UI v0.8 compliant card builder implementation."""

from typing import Any, Dict, List

from .base_card_builder import BaseCardBuilder
from helpers.generate_donut_chart import generate_donut_chart
from helpers.generate_horizontal_bar import generate_horizontal_bar
from helpers.generate_range_gauge import generate_range_gauge
from helpers.generate_status_pill import generate_status_pill
from helpers.generate_material_icon_svg import generate_material_icon_svg
from helpers.generate_number_widget import generate_number_widget
from helpers.generate_traffic_light_svg import generate_traffic_light_svg
from helpers.clean_payload import clean_payload


class CardBuilderV08(BaseCardBuilder):
    """Constructs layout and telemetry components for interactive A2UI status cards using v0.8 schema."""

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

        uptime_str = self._format_uptime(uptime)
        status_color = self._resolve_status_color(status)

        # Generate SVGs
        header_icon_uri = generate_material_icon_svg(icon_name, "#38BDF8")
        traffic_light_uri = generate_traffic_light_svg(status)

        components = self._load_template(
            "v08_card_base.json",
            {
                "header_icon_uri": header_icon_uri,
                "traffic_light_uri": traffic_light_uri,
                "name": name,
                "system_id": system_id,
                "sys_type_label": self.TYPE_LABELS.get(sys_type, "SYSTEM"),
                "status": status,
                "status_color": status_color,
                "description": description,
                "uptime_str": uptime_str,
            },
        )

        # Dynamic metrics content generation
        metrics_children_ids = []
        for m_spec in self.status.metrics:
            m_id = m_spec.id
            m_type = m_spec.type
            label = m_spec.label
            value = m_spec.value or 0.0
            val_text = m_spec.val_text or str(value)

            svg_data_uri = None
            if m_type == "donut_chart":
                svg_data_uri = generate_donut_chart(value, label)
            elif m_type == "progress_bar":
                svg_data_uri = generate_horizontal_bar(value, label, val_text)
            elif m_type == "range_gauge":
                max_value = m_spec.max_value or 100.0
                yellow_threshold = m_spec.yellow_threshold or 50.0
                red_threshold = m_spec.red_threshold or 80.0
                svg_data_uri = generate_range_gauge(
                    value, max_value, label, val_text, yellow_threshold, red_threshold
                )
            elif m_type == "status_pill":
                pill_status = m_spec.status or "healthy"
                svg_data_uri = generate_status_pill(label, val_text, pill_status)
            elif m_type == "number":
                svg_data_uri = generate_number_widget(label, val_text)

            if svg_data_uri:
                components.append(
                    self._load_template("metric_image.json", {"m_id": m_id, "svg_data_uri": svg_data_uri})
                )
                metrics_children_ids.append(m_id)
            else:
                fallback_txt_id = f"{m_id}-fallback-txt"
                components.append(
                    self._load_template(
                        "metric_text.json",
                        {"fallback_txt_id": fallback_txt_id, "label": label, "val_text": val_text},
                    )
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
                self._load_template(
                    "action_button.json",
                    {
                        "a_id": a_id,
                        "label": label,
                        "color": color,
                        "system_id": system_id,
                        "command": command,
                    },
                )
            )
            actions_children_ids.append(a_id)

        # Bind actions-row children
        for comp in components:
            if comp["id"] == "actions-row":
                comp["component"]["Row"]["children"]["explicitList"] = actions_children_ids

        return clean_payload(components)

    def build_logs_card(self) -> List[Dict[str, Any]]:
        """Assembles and returns list of A2UI components representing a dedicated logs viewer.

        Returns:
            List of dictionary components compliant with A2UI v0.8 specification.
        """
        system_id = self.status.system_id
        name = self.status.name
        status = self.status.status
        icon_name = "history"

        status_color = self._resolve_status_color(status)

        # Generate SVGs
        header_icon_uri = generate_material_icon_svg(icon_name, "#38BDF8")
        traffic_light_uri = generate_traffic_light_svg(status)

        components = self._load_template(
            "v08_logs_card_base.json",
            {
                "header_icon_uri": header_icon_uri,
                "traffic_light_uri": traffic_light_uri,
                "name": name,
                "system_id": system_id,
                "status": status,
                "status_color": status_color,
            },
        )

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
                self._load_template(
                    "log_line.json",
                    {
                        "log_id": log_id,
                        "log_text": log_text,
                        "color": color,
                    },
                )
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

        return clean_payload(components)
