"""Pydantic data model for router node metadata."""

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
