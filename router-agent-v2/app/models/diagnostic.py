"""Pydantic data model for diagnostic query results."""

from typing import Any
from pydantic import BaseModel, Field


class DiagnosticQueryResult(BaseModel):
    """Structured response for diagnostic telemetry queries."""

    status: str = Field(description="Execution result: 'success' or 'error'.")
    router_id: str | None = Field(default=None, description="Target router node ID.")
    data: dict[str, Any] | None = Field(
        default=None, description="Diagnostic payload data."
    )
    error: str | None = Field(default=None, description="Error message if failed.")
    recovery_instruction: str | None = Field(
        default=None, description="LLM recovery guidance on failure."
    )
