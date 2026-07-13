"""SNMP Emulation Helper Module for Router Emulator.

Provides MIB-II (RFC 1213) object resolution and formatting for HTTP-based 
SNMP emulation (snmpget, snmpwalk) over Cloud Run single-port HTTP ingress.
"""

import time
from typing import Any, Dict, List, Optional, Tuple

# Standard MIB-II Base OIDs
OID_SYS_DESCR = (1, 3, 6, 1, 2, 1, 1, 1, 0)
OID_SYS_OBJECT_ID = (1, 3, 6, 1, 2, 1, 1, 2, 0)
OID_SYS_UPTIME = (1, 3, 6, 1, 2, 1, 1, 3, 0)
OID_SYS_CONTACT = (1, 3, 6, 1, 2, 1, 1, 4, 0)
OID_SYS_NAME = (1, 3, 6, 1, 2, 1, 1, 5, 0)
OID_SYS_LOCATION = (1, 3, 6, 1, 2, 1, 1, 6, 0)
OID_SYS_SERVICES = (1, 3, 6, 1, 2, 1, 1, 7, 0)
OID_IF_NUMBER = (1, 3, 6, 1, 2, 1, 2, 1, 0)

# MIB OID Human Names Mapping
OID_NAMES: Dict[Tuple[int, ...], str] = {
    OID_SYS_DESCR: "SNMPv2-MIB::sysDescr.0",
    OID_SYS_OBJECT_ID: "SNMPv2-MIB::sysObjectID.0",
    OID_SYS_UPTIME: "DISMAN-EVENT-MIB::sysUpTimeInstance",
    OID_SYS_CONTACT: "SNMPv2-MIB::sysContact.0",
    OID_SYS_NAME: "SNMPv2-MIB::sysName.0",
    OID_SYS_LOCATION: "SNMPv2-MIB::sysLocation.0",
    OID_SYS_SERVICES: "SNMPv2-MIB::sysServices.0",
    OID_IF_NUMBER: "IF-MIB::ifNumber.0",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 1, 1): "IF-MIB::ifIndex.1",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 1, 2): "IF-MIB::ifIndex.2",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 1, 3): "IF-MIB::ifIndex.3",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 1, 4): "IF-MIB::ifIndex.4",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 1, 5): "IF-MIB::ifIndex.5",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 2, 1): "IF-MIB::ifDescr.1",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 2, 2): "IF-MIB::ifDescr.2",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 2, 3): "IF-MIB::ifDescr.3",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 2, 4): "IF-MIB::ifDescr.4",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 2, 5): "IF-MIB::ifDescr.5",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 8, 1): "IF-MIB::ifOperStatus.1",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 8, 2): "IF-MIB::ifOperStatus.2",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 8, 3): "IF-MIB::ifOperStatus.3",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 8, 4): "IF-MIB::ifOperStatus.4",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 8, 5): "IF-MIB::ifOperStatus.5",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 5, 1): "IF-MIB::ifSpeed.1",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 5, 2): "IF-MIB::ifSpeed.2",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 5, 3): "IF-MIB::ifSpeed.3",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 5, 4): "IF-MIB::ifSpeed.4",
    (1, 3, 6, 1, 2, 1, 2, 2, 1, 5, 5): "IF-MIB::ifSpeed.5",
}


def oid_to_tuple(oid_str: str) -> Tuple[int, ...]:
    """Converts a dotted OID string to a tuple of integers.

    Args:
        oid_str: Dotted OID string (e.g. '1.3.6.1.2.1.1.1.0' or '.1.3.6.1.2.1.1.1.0').

    Returns:
        Tuple of integers representing the OID sequence.
    """
    clean_str = oid_str.lstrip(".")
    parts = [x for x in clean_str.split(".") if x.isdigit()]
    return tuple(int(x) for x in parts)


def tuple_to_oid(oid_tuple: Tuple[int, ...]) -> str:
    """Converts a tuple of integers to a dotted OID string.

    Args:
        oid_tuple: Tuple of integers.

    Returns:
        Dotted string representation of the OID.
    """
    return "." + ".".join(str(x) for x in oid_tuple)


def get_mib_data(
    router_state: Dict[str, Any],
    router_metadata: Dict[str, str],
    start_time: float,
) -> Dict[Tuple[int, ...], Dict[str, Any]]:
    """Builds the dynamic MIB database dictionary containing OID types and formatted values.

    Args:
        router_state: Current in-memory router state dictionary.
        router_metadata: Router metadata configuration dictionary.
        start_time: System launch epoch timestamp.

    Returns:
        Dictionary mapping OID tuples to object details (value, type, name).
    """
    uptime_seconds = time.time() - start_time
    timeticks = int(uptime_seconds * 100)

    def is_link_up(led_key: str) -> Tuple[int, str]:
        state = str(router_state.get(led_key, "off")).lower()
        if state not in ("off", "red"):
            return (1, "up(1)")
        return (2, "down(2)")

    mfr = router_metadata.get("manufacturer_id", "CISCO-NEXUS-9000-X")
    fw = router_metadata.get("firmware_version", "v4.18.2-LTS")
    r_id = router_metadata.get("router_id", "RTR-CORE-01")
    loc = router_metadata.get("location", "Data Center Alpha")

    u_stat, u_str = is_link_up("upstream")
    l1_stat, l1_str = is_link_up("lan1")
    l2_stat, l2_str = is_link_up("lan2")
    l3_stat, l3_str = is_link_up("lan3")
    l4_stat, l4_str = is_link_up("lan4")

    mib: Dict[Tuple[int, ...], Dict[str, Any]] = {
        OID_SYS_DESCR: {"value": f"Router Emulator - {mfr} ({fw})", "type": "STRING"},
        OID_SYS_OBJECT_ID: {"value": ".1.3.6.1.4.1.9.1.1", "type": "OID"},
        OID_SYS_UPTIME: {"value": f"Timeticks: ({timeticks}) {int(uptime_seconds)}s", "type": "Timeticks"},
        OID_SYS_CONTACT: {"value": "Network Admin <admin@example.com>", "type": "STRING"},
        OID_SYS_NAME: {"value": r_id, "type": "STRING"},
        OID_SYS_LOCATION: {"value": loc, "type": "STRING"},
        OID_SYS_SERVICES: {"value": 78, "type": "INTEGER"},
        OID_IF_NUMBER: {"value": 5, "type": "INTEGER"},

        # Interfaces
        (1, 3, 6, 1, 2, 1, 2, 2, 1, 1, 1): {"value": 1, "type": "INTEGER"},
        (1, 3, 6, 1, 2, 1, 2, 2, 1, 1, 2): {"value": 2, "type": "INTEGER"},
        (1, 3, 6, 1, 2, 1, 2, 2, 1, 1, 3): {"value": 3, "type": "INTEGER"},
        (1, 3, 6, 1, 2, 1, 2, 2, 1, 1, 4): {"value": 4, "type": "INTEGER"},
        (1, 3, 6, 1, 2, 1, 2, 2, 1, 1, 5): {"value": 5, "type": "INTEGER"},

        (1, 3, 6, 1, 2, 1, 2, 2, 1, 2, 1): {"value": "Upstream-0", "type": "STRING"},
        (1, 3, 6, 1, 2, 1, 2, 2, 1, 2, 2): {"value": "LAN-1", "type": "STRING"},
        (1, 3, 6, 1, 2, 1, 2, 2, 1, 2, 3): {"value": "LAN-2", "type": "STRING"},
        (1, 3, 6, 1, 2, 1, 2, 2, 1, 2, 4): {"value": "LAN-3", "type": "STRING"},
        (1, 3, 6, 1, 2, 1, 2, 2, 1, 2, 5): {"value": "LAN-4", "type": "STRING"},

        (1, 3, 6, 1, 2, 1, 2, 2, 1, 8, 1): {"value": u_str, "raw": u_stat, "type": "INTEGER"},
        (1, 3, 6, 1, 2, 1, 2, 2, 1, 8, 2): {"value": l1_str, "raw": l1_stat, "type": "INTEGER"},
        (1, 3, 6, 1, 2, 1, 2, 2, 1, 8, 3): {"value": l2_str, "raw": l2_stat, "type": "INTEGER"},
        (1, 3, 6, 1, 2, 1, 2, 2, 1, 8, 4): {"value": l3_str, "raw": l3_stat, "type": "INTEGER"},
        (1, 3, 6, 1, 2, 1, 2, 2, 1, 8, 5): {"value": l4_str, "raw": l4_stat, "type": "INTEGER"},

        (1, 3, 6, 1, 2, 1, 2, 2, 1, 5, 1): {"value": "1000000000", "type": "Gauge32"},
        (1, 3, 6, 1, 2, 1, 2, 2, 1, 5, 2): {"value": "1000000000", "type": "Gauge32"},
        (1, 3, 6, 1, 2, 1, 2, 2, 1, 5, 3): {"value": "1000000000", "type": "Gauge32"},
        (1, 3, 6, 1, 2, 1, 2, 2, 1, 5, 4): {"value": "1000000000", "type": "Gauge32"},
        (1, 3, 6, 1, 2, 1, 2, 2, 1, 5, 5): {"value": "1000000000", "type": "Gauge32"},
    }

    # Add OID string & Human Name to each item
    for oid, obj in mib.items():
        obj["oid"] = tuple_to_oid(oid)
        obj["name"] = OID_NAMES.get(oid, f"ISO.org.dod.internet.mgmt.mib-2.{obj['oid']}")

    return mib


def format_snmpwalk_output(mib_data: Dict[Tuple[int, ...], Dict[str, Any]]) -> str:
    """Formats the MIB database into standard snmpwalk CLI text output.

    Args:
        mib_data: MIB database dictionary.

    Returns:
        Multiline text string formatted as snmpwalk output.
    """
    lines: List[str] = []
    for oid_tuple in sorted(mib_data.keys()):
        item = mib_data[oid_tuple]
        name = item["name"]
        val = item["value"]
        val_type = item["type"]
        lines.append(f"{name} = {val_type}: {val}")
    return "\n".join(lines)
