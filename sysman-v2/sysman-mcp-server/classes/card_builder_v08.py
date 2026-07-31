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
from helpers.generate_material_icon_svg import generate_material_icon_svg
from helpers.generate_traffic_light_svg import generate_traffic_light_svg
from helpers.generate_metrics_components import generate_metrics_components
from helpers.generate_action_components import generate_action_components
from helpers.generate_log_components import generate_log_components
from helpers.clean_payload import clean_payload


class CardBuilderV08(BaseCardBuilder):
    """Concrete A2UI v0.8 card builder implementation.

    This builder decouples UI structure declarations from business logic by loading static layout
    JSON templates from the `templates/` directory. Placeholders (e.g. `{{name}}`) in templates
    are dynamically replaced at load time.

    The builder delegates low-level metric loops, button packaging, and console logs generation
    to specialized helpers.
    """

    def build(self) -> List[Dict[str, Any]]:
        """Assembles and returns a complete list of A2UI components representing the system.

        This method orchestrates card generation by:
        1. Loading the base card container shell from `v08_card_base.json`.
        2. Delegating metric chart generation to `generate_metrics_components`.
        3. Dynamically binding grid rows to the parent column container.
        4. Delegating action control buttons generation to `generate_action_components`.
        5. Binding action buttons to the action row container.

        Returns:
            List of dictionary components compliant with the A2UI v0.8 specification.
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

        # Generate SVGs for status card widgets
        header_icon_uri = generate_material_icon_svg(icon_name, "#38BDF8")
        traffic_light_uri = generate_traffic_light_svg(status)

        # Step 1: Load base card container structure with basic system details
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

        # Step 2: Generate system metrics components and group them into grid rows
        metric_components, grid_rows_ids = generate_metrics_components(
            self.status.metrics, self._load_template
        )
        components.extend(metric_components)

        # Step 3: Explicit Layout Data Binding - parent container nodes in A2UI must
        # explicitly register the IDs of their children inside the `explicitList` property.
        # Here we bind the generated grid row IDs to the parent 'metrics-column' component.
        for comp in components:
            if comp["id"] == "metrics-column":
                comp["component"]["Column"]["children"]["explicitList"] = grid_rows_ids

        # Step 4: Generate action buttons dynamically
        action_components, actions_children_ids = generate_action_components(
            self.status.actions, system_id, self._load_template
        )
        components.extend(action_components)

        # Step 5: Bind action buttons to the bottom 'actions-row' Row container
        for comp in components:
            if comp["id"] == "actions-row":
                comp["component"]["Row"]["children"]["explicitList"] = actions_children_ids

        return clean_payload(components)

    def build_logs_card(self) -> List[Dict[str, Any]]:
        """Assembles and returns a list of A2UI components representing a dedicated logs viewer.

        This method orchestrates log card generation by:
        1. Loading the base log card container shell from `v08_logs_card_base.json`.
        2. Resolving log entries and colorizing levels (DEBUG, INFO, etc.) via helper.
        3. Appending the scrollable log console stream window to the main column.

        Returns:
            List of dictionary components compliant with the A2UI v0.8 specification.
        """
        system_id = self.status.system_id
        name = self.status.name
        status = self.status.status
        icon_name = "history"

        status_color = self._resolve_status_color(status)

        # Generate status SVGs for the header
        header_icon_uri = generate_material_icon_svg(icon_name, "#38BDF8")
        traffic_light_uri = generate_traffic_light_svg(status)

        # Step 1: Load base logs container structure
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

        # Step 2: Generate log level colored stream components
        log_components, logs_children = generate_log_components(
            self.status.logs, self._load_template
        )
        components.extend(log_components)

        # Step 3: Append the scrollable console window containing all generated log components
        components.append(
            self._load_template("logs_console.json", {"logs_children": logs_children})
        )

        return clean_payload(components)
