"""Pydantic data model for request classification."""

from typing import Literal
from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    """Result of classifying a user request."""
    
    route: Literal["diagnostic", "remediation", "fallback"] = Field(
        description="Route to 'diagnostic' for telemetry/status/logs, 'remediation' for actions (reboot, led, etc), or 'fallback' for general queries."
    )
    router_id: str | None = Field(
        default=None,
        description="Target router ID if mentioned in the query."
    )
