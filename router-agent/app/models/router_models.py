"""Pydantic data models for Router Fleet Operations ADK Agent."""

from typing import Any

from pydantic import BaseModel, Field


class RouterNodeMetadata(BaseModel):
    """Router node metadata representation."""

    id: str = Field(description="Unique hardware router identifier.")
    name: str = Field(description="Human-readable node display name.")
    location: str = Field(description="Physical datacenter or cloud region.")
    purpose: str = Field(description="Network role or service description.")
    url: str = Field(description="Direct management endpoint URL.")
    source: str = Field(
        default="CLOUDRUN", description="Deployment infrastructure type."
    )


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
