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

"""Abstract base class for A2UI card builders."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from models import SystemStatus


class BaseCardBuilder(ABC):
    """Abstract base class for constructing layout and telemetry components for A2UI status cards.

    Contains version-agnostic metadata extraction, status resolving, and formatting helpers.
    """

    TYPE_LABELS = {
        "jira": "JIRA APP",
        "confluence": "CONFLUENCE APP",
        "linux": "LINUX VM",
    }

    def __init__(self, system_status: SystemStatus, surface_id: str) -> None:
        """Initializes the builder with system status and surface context.

        Args:
            system_status: SystemStatus model containing telemetry data.
            surface_id: Unique string surface identifier for the card rendering session.
        """
        self.status = system_status
        self.surface_id = surface_id

    @abstractmethod
    def build(self) -> List[Dict[str, Any]]:
        """Assembles and returns a list of A2UI components representing the system.

        Returns:
            List of dictionary components compliant with the target A2UI specification.
        """
        pass

    @abstractmethod
    def build_logs_card(self) -> List[Dict[str, Any]]:
        """Assembles and returns a list of A2UI components representing a dedicated logs viewer.

        Returns:
            List of dictionary components compliant with the target A2UI specification.
        """
        pass

    def _format_uptime(self, uptime: int) -> str:
        """Formats uptime in seconds into a human-readable day/hour/minute/second string."""
        d = uptime // 86400
        h = (uptime % 86400) // 3600
        m = (uptime % 3600) // 60
        s = uptime % 60
        return f"{d}d {h}h {m}m {s}s"

    def _resolve_status_color(self, status: str) -> str:
        """Resolves system health status string to a hex color code."""
        if status == "DEGRADED":
            return "#F59E0B"
        elif status in ("UNHEALTHY", "REBOOTING", "UNKNOWN"):
            return "#EF4444"
        return "#22C55E"
