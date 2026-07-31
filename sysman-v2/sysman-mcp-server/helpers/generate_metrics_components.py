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

"""Helper to generate metrics components and their grid layout rows."""

from typing import Any, Callable, Dict, List, Tuple

from .generate_donut_chart import generate_donut_chart
from .generate_horizontal_bar import generate_horizontal_bar
from .generate_number_widget import generate_number_widget
from .generate_range_gauge import generate_range_gauge
from .generate_status_pill import generate_status_pill


def generate_metrics_components(
    metrics: List[Any],
    load_template_fn: Callable[[str, Dict[str, Any]], Any]
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Generates components and layout rows for telemetry metrics.

    Args:
        metrics: List of metric models/specifications to render.
        load_template_fn: Function to load template files with substituted placeholders.

    Returns:
        A tuple of (generated_components, grid_rows_ids).
    """
    components: List[Dict[str, Any]] = []
    metrics_children_ids: List[str] = []

    for m_spec in metrics:
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
                load_template_fn("metric_image.json", {"m_id": m_id, "svg_data_uri": svg_data_uri})
            )
            metrics_children_ids.append(m_id)
        else:
            fallback_txt_id = f"{m_id}-fallback-txt"
            components.append(
                load_template_fn(
                    "metric_text.json",
                    {"fallback_txt_id": fallback_txt_id, "label": label, "val_text": val_text},
                )
            )
            metrics_children_ids.append(fallback_txt_id)

    # Lay out metrics in a 4-column grid (up to 4 per row)
    grid_rows_ids: List[str] = []
    for i in range(0, len(metrics_children_ids), 4):
        row_id = f"metrics-row-{i//4}"
        row_children = metrics_children_ids[i : i + 4]
        components.append(
            load_template_fn(
                "metrics_row.json", {"row_id": row_id, "row_children": row_children}
            )
        )
        grid_rows_ids.append(row_id)

    return components, grid_rows_ids
