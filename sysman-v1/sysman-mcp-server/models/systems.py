"""Pydantic models representing System states, metrics, actions and logs."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SystemMetadata(BaseModel):
    """Metadata representing a single virtual system in the fleet."""
    system_id: str = Field(..., description="Unique system identifier.")
    name: str = Field(..., description="Human-readable name of the system.")
    type: str = Field(..., description="Type of the system (e.g. linux, jira, confluence).")
    status: str = Field(..., description="Overall health/status of the system (e.g. HEALTHY, DEGRADED).")


class LogEntry(BaseModel):
    """A single diagnostic log entry."""
    level: str = Field(..., description="Log level (e.g. INFO, WARNING, ERROR).")
    timestamp: str = Field(..., description="ISO or relative timestamp of the log entry.")
    message: str = Field(..., description="Actual log message content.")


class MetricSpec(BaseModel):
    """Specification of a system metric telemetry instrument."""
    id: str = Field(..., description="Unique metric identifier.")
    type: str = Field(..., description="Type of visualization widget (e.g. donut_chart, progress_bar, range_gauge, status_pill, number).")
    label: str = Field(..., description="Label description of the metric.")
    value: Optional[float] = Field(None, description="Numeric value of the metric.")
    val_text: Optional[str] = Field(None, description="Formatted text representation of the value.")
    max_value: Optional[float] = Field(None, description="Maximum scale value for range_gauge.")
    yellow_threshold: Optional[float] = Field(None, description="Yellow warning threshold for range_gauge.")
    red_threshold: Optional[float] = Field(None, description="Red critical threshold for range_gauge.")
    status: Optional[str] = Field(None, description="Status string for status_pill (e.g. healthy, warning, critical).")


class ActionSpec(BaseModel):
    """Specification of a system control action."""
    id: str = Field(..., description="Unique action identifier.")
    label: str = Field(..., description="Button display label.")
    command: str = Field(..., description="Command string executed when clicked.")
    color: Optional[str] = Field(None, description="Action hex color representation.")


class SystemStatus(BaseModel):
    """Detailed configuration-driven system status state."""
    system_id: str = Field(..., description="Unique system identifier.")
    type: str = Field(..., description="Type of system (e.g. linux, jira, confluence).")
    name: str = Field(..., description="Human-readable name.")
    status: str = Field(..., description="Current status of the system.")
    description: str = Field("", description="Short description of the system.")
    uptime_seconds: int = Field(..., description="Uptime duration in seconds.")
    default_icon: str = Field("business_center", description="Default Material icon name.")
    logs: List[LogEntry] = Field(default_factory=list, description="Recent diagnostic logs.")
    metrics: List[MetricSpec] = Field(default_factory=list, description="List of system metrics.")
    actions: List[ActionSpec] = Field(default_factory=list, description="List of support operations actions.")
