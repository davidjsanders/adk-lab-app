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

"""Number status card widget generator."""

from .template_renderer import render_svg_template


def generate_number_widget(label: str, val_text: str) -> str:
    """Generates a Base64-encoded SVG card showing a prominent numeric value/text.

    Args:
        label: Description header of the numeric metric.
        val_text: Display string of the numeric value (e.g. "5 entries", "12 users").

    Returns:
        Data URI string formatted as data:image/svg+xml;base64,...
    """
    label_len = len(label)
    font_size = 4.0 if label_len > 24 else (5.0 if label_len > 18 else 6.0)

    val_len = len(val_text)
    val_font_size = 8.0 if val_len > 12 else (10.0 if val_len > 8 else 12.0)

    replacements = {
        "FONT_SIZE": f"{font_size:.1f}",
        "LABEL": label,
        "VAL_FONT_SIZE": f"{val_font_size:.1f}",
        "VAL_TEXT": val_text
    }
    return render_svg_template("number_widget", replacements)
