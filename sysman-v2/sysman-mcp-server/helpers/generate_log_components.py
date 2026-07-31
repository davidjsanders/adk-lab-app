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

"""Helper to generate console log components and color-code severity."""

from typing import Any, Callable, Dict, List, Tuple


def generate_log_components(
    logs: List[Any],
    load_template_fn: Callable[[str, Dict[str, Any]], Any]
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Generates console text components for log streams and applies level colors.

    Args:
        logs: List of log models to generate.
        load_template_fn: Function to load template files with substituted placeholders.

    Returns:
        A tuple of (generated_components, logs_children_ids).
    """
    components: List[Dict[str, Any]] = []
    logs_children: List[str] = []

    for index, log in enumerate(logs):
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
            load_template_fn(
                "log_line.json",
                {
                    "log_id": log_id,
                    "log_text": log_text,
                    "color": color,
                },
            )
        )
        logs_children.append(log_id)

    return components, logs_children
