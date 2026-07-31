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

"""Horizontal progress bar generator."""

from .template_renderer import render_svg_template


def generate_horizontal_bar(percentage: float, label: str, val_text: str) -> str:
    """Generates a Base64-encoded SVG horizontal progress bar.

    Args:
        percentage: The progress percentage value (0.0 to 100.0).
        label: Text label describing the progress bar.
        val_text: Raw display value text printed adjacent to the label.

    Returns:
        Data URI string formatted as data:image/svg+xml;base64,...
    """
    percentage = max(0.0, min(100.0, percentage))
    fill_width = percentage * 0.6

    label_len = len(label)
    font_size = 4.0 if label_len > 24 else (5.0 if label_len > 18 else 6.0)

    replacements = {
        "FONT_SIZE": f"{font_size:.1f}",
        "LABEL": label,
        "FILL_WIDTH": f"{fill_width:.2f}",
        "VAL_TEXT": val_text
    }
    return render_svg_template("horizontal_bar", replacements)
