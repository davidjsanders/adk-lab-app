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

"""Google Material Design Icon generator."""

from typing import Dict
from .template_renderer import render_svg_template

MATERIAL_ICONS: Dict[str, str] = {
    "dns": "M20,13H4C2.9,13,2,13.9,2,15v4c0,1.1,0.9,2,2,2h16c1.1,0,2-0.9,2-2v-4C22,13.9,21.1,13,20,13z M20,19H4v-4h16V19z M20,3H4 C2.9,3,2,3.9,2,5v4c0,1.1,0.9,2,2,2h16c1.1,0,2-0.9,2-2V5C22,3.9,21.1,3,20,3z M20,9H4V5h16V9z",
    "business_center": "M20 7h-4V5c0-1.1-.9-2-2-2h-4c-1.1 0-2 .9-2 2v2H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V9c0-1.1-.9-2-2-2zM10 5h4v2h-4V5zm10 14H4V9h16v10z",
    "article": "M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zm-4-4H9v-2h6v2zm-2-4H9V9h4v2z",
    "confirmation_number": "M22 10V6c0-1.11-.9-2-2-2H4c-1.1 0-1.99.89-1.99 2v4c1.1 0 1.99.9 1.99 2s-.89 2-2 2v4c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2v-4c-1.1 0-2-.9-2-2s.9-2 2-2zm-9 7.5h-2v-2h2v2zm0-4.5h-2v-2h2v2zm0-4.5h-2v-2h2v2z",
    "computer": "M20 18c1.1 0 1.99-.9 1.99-2L22 6c0-1.1-.9-2-2-2H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2H0v2h24v-2h-4zM4 6h16v10H4V6z",
    "history": "M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"
}


def generate_material_icon_svg(icon_name: str, fill_color: str = "#38BDF8") -> str:
    """Generates a Base64-encoded Data URI for a Google Material Design Icon SVG path.

    Args:
        icon_name: Name of the Google Font icon (e.g. 'dns', 'business_center', 'article').
        fill_color: Hex color string.

    Returns:
        Data URI string formatted as data:image/svg+xml;base64,...
    """
    path_d = MATERIAL_ICONS.get(icon_name, MATERIAL_ICONS["business_center"])
    replacements = {
        "PATH_D": path_d,
        "FILL_COLOR": fill_color
    }
    return render_svg_template("material_icon", replacements)
