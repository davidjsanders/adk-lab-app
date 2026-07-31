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

"""Traffic light health indicator generator."""

from .template_renderer import render_svg_template


def generate_traffic_light_svg(status: str) -> str:
    """Generates a Base64-encoded Data URI for a dynamic traffic light SVG.

    Args:
        status: The system health status string.

    Returns:
        Data URI string formatted as data:image/svg+xml;base64,...
    """
    red_color = "#7F1D1D"     # Saturated dull red
    amber_color = "#78350F"   # Saturated dull amber
    green_color = "#064E3B"   # Saturated dull green

    if status == "HEALTHY":
        green_color = "#00FF66"  # Brighter electric green
    elif status == "DEGRADED":
        amber_color = "#F59E0B"
    else:  # UNHEALTHY, REBOOTING, etc.
        red_color = "#EF4444"

    replacements = {
        "RED_COLOR": red_color,
        "AMBER_COLOR": amber_color,
        "GREEN_COLOR": green_color
    }
    return render_svg_template("traffic_light", replacements)
