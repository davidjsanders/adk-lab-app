from enum import StrEnum

class CallbackSkips(StrEnum):
    """List of tools to skip callback processing for."""
    LIST_SKILLS = "list_skills"
    LOAD_SKILL = "load_skill"
