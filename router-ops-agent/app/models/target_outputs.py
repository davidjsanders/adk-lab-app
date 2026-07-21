from enum import StrEnum

class TargetOutput(StrEnum):
    """List of tools to skip callback processing for."""
    A2UI_JSON = "<a2ui-json>"
    DATA_IMAGE_PNG = "data:image/png;base64,"
