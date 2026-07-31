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

"""Range gauge pointer scale generator."""

from .template_renderer import render_svg_template


def generate_range_gauge(
    value: float,
    max_value: float,
    label: str,
    val_text: str,
    yellow_threshold: float,
    red_threshold: float
) -> str:
    """Generates a Base64-encoded SVG range gauge scale with a pointer indicator.

    Args:
        value: Current metric value.
        max_value: Target maximum bounds of the scale (maps to 100% width).
        label: Metric label description.
        val_text: Display value string.
        yellow_threshold: Yellow warning boundary metric value.
        red_threshold: Red critical boundary metric value.

    Returns:
        Data URI string formatted as data:image/svg+xml;base64,...
    """
    percentage = (value / max_value) * 100.0 if max_value > 0 else 0.0
    percentage = max(0.0, min(100.0, percentage))

    yellow_pct = (yellow_threshold / max_value) * 100.0 if max_value > 0 else 50.0
    red_pct = (red_threshold / max_value) * 100.0 if max_value > 0 else 80.0

    ptr_x = 10 + (percentage * 0.6)

    label_len = len(label)
    font_size = 4.0 if label_len > 24 else (5.0 if label_len > 18 else 6.0)

    replacements = {
        "FONT_SIZE": f"{font_size:.1f}",
        "LABEL": label,
        "YELLOW_PCT_WIDTH": f"{yellow_pct * 0.6:.2f}",
        "YELLOW_START_X": f"{10 + yellow_pct * 0.6:.2f}",
        "YELLOW_TO_RED_WIDTH": f"{(red_pct - yellow_pct) * 0.6:.2f}",
        "RED_START_X": f"{10 + red_pct * 0.6:.2f}",
        "RED_TO_END_WIDTH": f"{(100 - red_pct) * 0.6:.2f}",
        "PTR_X": f"{ptr_x:.2f}",
        "PTR_X_MINUS_3": f"{ptr_x - 3:.2f}",
        "PTR_X_PLUS_3": f"{ptr_x + 3:.2f}",
        "VAL_TEXT": val_text
    }
    return render_svg_template("range_gauge", replacements)
