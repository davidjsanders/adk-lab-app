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

"""Status pill banner widget generator."""

from .template_renderer import render_svg_template


def generate_status_pill(label: str, val_text: str, status: str) -> str:
    """Generates a Base64-encoded SVG status banner pill with a custom icon.

    Args:
        label: Status metric label description.
        val_text: Formatted display text state.
        status: One of 'healthy', 'warning', or 'critical'.

    Returns:
        Data URI string formatted as data:image/svg+xml;base64,...
    """
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

    replacements = {
        "FONT_SIZE": f"{font_size:.1f}",
        "LABEL": label,
        "BG_COLOR": bg_color,
        "BORDER_COLOR": border_color,
        "ICON_PATH": icon_path,
        "TEXT_COLOR": text_color,
        "VAL_TEXT": val_text
    }
    return render_svg_template("status_pill", replacements)
