"""Pydantic data model for remediation results."""

from typing import Any
from pydantic import BaseModel, Field


class RemediationResult(BaseModel):
    """Structured response for hardware remediation actions."""

    status: str = Field(
        description="Execution status: 'success', 'pending_approval', or 'error'."
    )
    action: str = Field(description="Remediation action performed.")
    router_id: str = Field(description="Target router node ID.")
    message: str = Field(description="Execution result summary message.")
    state: dict[str, Any] | None = Field(
        default=None, description="Post-action state metadata."
    )
    error: str | None = Field(default=None, description="Error message if failed.")
    recovery_instruction: str | None = Field(
        default=None, description="Guidance for LLM recovery."
    )
