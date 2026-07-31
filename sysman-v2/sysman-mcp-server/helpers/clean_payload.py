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

"""Helper utility to clean layout payload structures for rendering compatibility."""

from typing import Any


def clean_payload(obj: Any) -> Any:
    """Recursively removes all 'style' keys and replaces invalid 'body1' typography usage hints.

    Rationale:
    1. A2UI v0.8 Schema Compliance: The standard A2UI specification does not support custom CSS-like
       styling attributes (e.g., backgroundColor, padding, borderRadius) at the component structure level.
       Instead, elements are styled dynamically by the client host's active theme.
    2. Blueprint Reference: The component blueprints in `CardBuilder` include these styling parameters
       to document the original design intent for developers, acting as an inline visual layout guide.
    3. Safety Translation: Translates common typography mismatches (such as changing the invalid token
       'body1' into the compliant 'body' token) to avoid platform-level rendering errors.

    Using this post-processor allows developers to retain visual styling documentation in-line
    without breaking strict A2UI v0.8 schemas.

    Args:
        obj: The layout component structure dictionary or list.

    Returns:
        The cleaned, A2UI-compliant object.
    """
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            if key == "style":
                del obj[key]
            else:
                if key == "usageHint" and obj[key] == "body1":
                    obj[key] = "body"
                clean_payload(obj[key])
    elif isinstance(obj, list):
        for item in obj:
            clean_payload(item)
    return obj
