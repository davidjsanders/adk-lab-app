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

"""Helper to generate action button components dynamically."""

from typing import Any, Callable, Dict, List, Tuple


def generate_action_components(
    actions: List[Any],
    system_id: str,
    load_template_fn: Callable[[str, Dict[str, Any]], Any]
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Generates control button components and lists their action IDs.

    Args:
        actions: List of action specifications containing labels and commands.
        system_id: The identifier of the system these actions are bound to.
        load_template_fn: Function to load template files with substituted placeholders.

    Returns:
        A tuple of (generated_components, actions_children_ids).
    """
    components: List[Dict[str, Any]] = []
    actions_children_ids: List[str] = []

    for a_spec in actions:
        a_id = a_spec.id
        label = a_spec.label
        command = a_spec.command
        color = a_spec.color or "#00FF00"
        components.extend(
            load_template_fn(
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

    return components, actions_children_ids
