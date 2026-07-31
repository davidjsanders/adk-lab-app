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

"""Backward-compatible A2UI CardBuilder factory routing to versioned concrete builders."""

from typing import Any, Dict, List
from models import SystemStatus
from .base_card_builder import BaseCardBuilder


class CardBuilder:
    """Facade proxy class routing card generation to versioned builders (e.g. CardBuilderV08)."""

    def __init__(self, system_status: SystemStatus, surface_id: str, version: str = "v0.8") -> None:
        """Initializes the CardBuilder proxy routing to the requested A2UI version.

        Args:
            system_status: SystemStatus model containing telemetry data.
            surface_id: Unique string surface identifier for the card rendering session.
            version: Target A2UI version string (defaults to "v0.8").
        """
        self.version = version
        if version == "v0.8":
            from .card_builder_v08 import CardBuilderV08
            self._impl: BaseCardBuilder = CardBuilderV08(system_status, surface_id)
        else:
            raise ValueError(f"Unsupported A2UI version: {version}")

    def build(self) -> List[Dict[str, Any]]:
        """Assembles and returns a list of components compliant with the target version's A2UI schema."""
        return self._impl.build()

    def build_logs_card(self) -> List[Dict[str, Any]]:
        """Assembles and returns a list of components compliant with the target version's A2UI schema."""
        return self._impl.build_logs_card()
