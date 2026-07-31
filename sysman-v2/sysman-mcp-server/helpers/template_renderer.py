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

"""Helper utility to render and encode SVG chart templates to Base64 Data URIs."""

import base64
import os
from typing import Dict, Any


def render_svg_template(template_name: str, replacements: Dict[str, Any]) -> str:
    """Loads a template file, replaces placeholders, and returns a Base64 Data URI.

    Args:
        template_name: The filename of the SVG template (without .svg).
        replacements: Dict of key/value pairs to replace in the SVG file.

    Returns:
        Data URI string formatted as data:image/svg+xml;base64,...
    """
    template_path = os.path.join(
        os.path.dirname(__file__), "..", "templates", f"{template_name}.svg"
    )
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"SVG Template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    for key, value in replacements.items():
        content = content.replace(f"{{{{{key}}}}}", str(value))

    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"
