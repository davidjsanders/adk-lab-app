"""Troubleshooting Knowledge Base class definition for SOP grounding queries."""

import logging
from typing import Any, ClassVar

logger = logging.getLogger("router-agent.classes.grounding")


class TroubleshootingKnowledgeBase:
    """Class representing the local SOP database and Vertex AI Search grounding resolver."""

    DEFAULT_SOP_DATABASE: ClassVar[dict[str, dict[str, Any]]] = {
        "BGP_DOWN": {
            "issue": "BGP Peering Session State DOWN / Disconnected",
            "description": "BGP border gateway protocol session is in failure mode or peering lost.",
            "recommended_steps": [
                "1. Verify upstream physical link LED status (upstream LED should be green).",
                "2. Execute fetch_router_hardware_logs to inspect for BGP state change events or connection timeouts.",
                "3. Run reset_router_bgp_peering to issue a BGP_RESET command restoring peering tables.",
                "4. If reset fails to restore peering within 30 seconds, execute reboot_router_chassis to clear socket state.",
            ],
            "severity": "CRITICAL",
        },
        "CHASSIS_OVERHEAT": {
            "issue": "Chassis Thermal Warning or Fan Degradation",
            "description": "Power/chassis LED amber or red, high internal CPU/thermal telemetry.",
            "recommended_steps": [
                "1. Run get_router_telemetry_status to review chassis LEDs.",
                "2. Issue set_router_chassis_led setting online LED to amber to signal maintenance mode.",
                "3. Schedule diagnostic reboot via reboot_router_chassis.",
            ],
            "severity": "HIGH",
        },
        "PACKET_LOSS": {
            "issue": "Elevated Interface Dropped Packets or Traffic Burst Anomaly",
            "description": "SNMP walk metrics indicate high interface errors or buffer congestion.",
            "recommended_steps": [
                "1. Run run_router_snmp_walk on OID '.1.3.6.1.2.1.2' to inspect interface counters.",
                "2. Inspect recent action logs via fetch_router_hardware_logs.",
                "3. If error rates persist, perform BGP peering reset to recalculate path metrics.",
            ],
            "severity": "MEDIUM",
        },
    }

    def __init__(self, datastore_id: str):
        """Initializes TroubleshootingKnowledgeBase with target Datastore ID.

        Args:
            datastore_id: Fully qualified datastore ID string for Vertex AI Search.

        Returns:
            None.

        Raises:
            None.
        """
        self.datastore_id = datastore_id

    def search(self, query: str) -> dict[str, Any]:
        """Searches SOP database and troubleshooting manuals matching input query.

        Args:
            query: Fault symptoms or error query text string.

        Returns:
            Dict containing query results, matching SOP articles, and datastore metadata.

        Raises:
            None.
        """
        query_lower = query.lower()
        matches: list[dict[str, Any]] = []

        for key, sop in self.DEFAULT_SOP_DATABASE.items():
            if key.lower() in query_lower or any(
                word in sop["description"].lower() or word in sop["issue"].lower()
                for word in query_lower.split()
            ):
                matches.append(sop)

        if not matches:
            matches.append(
                {
                    "issue": "General Router Fleet Operational Recovery Protocol",
                    "description": f"Standard recovery protocol for query: '{query}'.",
                    "recommended_steps": [
                        "1. Gather baseline node telemetry with get_router_telemetry_status.",
                        "2. Query node action logs with fetch_router_hardware_logs for ERROR level events.",
                        "3. Perform reset_router_bgp_peering if protocol session errors are detected.",
                        "4. Request human confirmation prior to dispatching reboot_router_chassis.",
                    ],
                    "severity": "INFO",
                }
            )

        return {
            "status": "success",
            "query": query,
            "datastore_id": self.datastore_id,
            "results_count": len(matches),
            "knowledge_articles": matches,
        }
