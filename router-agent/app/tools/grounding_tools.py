"""Troubleshooting knowledge grounding search tool."""

import logging
from typing import Any

from app.classes import TroubleshootingKnowledgeBase
from app.config import VERTEX_AI_SEARCH_DATASTORE_ID

logger = logging.getLogger("router-agent.tools.grounding")

# Instantiate Troubleshooting Knowledge Base grounding instance from app.classes
_KNOWLEDGE_BASE = TroubleshootingKnowledgeBase(
    datastore_id=VERTEX_AI_SEARCH_DATASTORE_ID
)


def search_troubleshooting_knowledge_base(query: str) -> dict[str, Any]:
    """Queries Vertex AI Search datastore and operational manuals to retrieve troubleshooting procedures for router faults.

    Args:
        query: Search query text describing the network fault or error symptom (e.g. 'BGP peering down error', 'Chassis overheat LED red').

    Returns:
        Dict containing matching troubleshooting procedures, standard operating procedures (SOPs), and action steps.

    Raises:
        RuntimeError: If grounding search fails.
    """
    return _KNOWLEDGE_BASE.search(query)
