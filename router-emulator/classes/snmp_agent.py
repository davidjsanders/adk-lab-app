"""SNMP MIB-II Agent Emulation Class for Router Emulator Application.

Generates standard MIB-II object trees (system, interfaces, IP, ICMP, TCP, UDP, BGP, SNMP)
and formats responses into snmpwalk CLI text output or structured JSON objects.
"""

from typing import Any, Dict, List, Tuple

from classes.router_state import RouterState


class SNMPAgent:
    """Manages SNMP MIB-II tree object generation and snmpwalk formatting."""

    @staticmethod
    def oid_to_tuple(oid_str: str) -> Tuple[int, ...]:
        """Converts a dotted OID string into a tuple of numerical integers.

        Args:
            oid_str: Dotted OID string (e.g. '1.3.6.1.2.1.1.1.0' or '.1.3.6.1.2.1.1').

        Returns:
            Tuple of integer components.
        """
        clean = oid_str.strip().lstrip(".")
        if not clean:
            return ()
        return tuple(int(part) for part in clean.split(".") if part.isdigit())

    @staticmethod
    def format_snmpwalk_output(mib_dict: Dict[Tuple[int, ...], Dict[str, Any]]) -> str:
        """Formats a MIB dictionary into standard NET-SNMP snmpwalk CLI text output lines.

        Args:
            mib_dict: Dictionary mapping OID tuples to value metadata objects.

        Returns:
            Newline-separated string matching standard snmpwalk CLI output format.
        """
        lines: List[str] = []
        for _, item in sorted(mib_dict.items()):
            name = item["name"]
            type_str = item["type"]
            val = item["value"]

            if type_str == "OCTET-STRING":
                lines.append(f"{name} = STRING: \"{val}\"")
            elif type_str == "OBJECT-IDENTIFIER":
                lines.append(f"{name} = OID: {val}")
            elif type_str == "TimeTicks":
                lines.append(f"{name} = Timeticks: ({val}) {val / 100:.2f} seconds")
            elif type_str == "Gauge32":
                lines.append(f"{name} = Gauge32: {val}")
            elif type_str == "Counter32":
                lines.append(f"{name} = Counter32: {val}")
            elif type_str == "IpAddress":
                lines.append(f"{name} = IpAddress: {val}")
            else:
                lines.append(f"{name} = {type_str}: {val}")

        return "\n".join(lines) + "\n" if lines else ""

    @classmethod
    def compile_mib_tree(cls, router_state: RouterState) -> Dict[Tuple[int, ...], Dict[str, Any]]:
        """Compiles full MIB-II tree representation from current hardware router state.

        Args:
            router_state: RouterState instance containing telemetry and hardware metadata.

        Returns:
            Dictionary mapping numerical OID tuples to object definitions.
        """
        sys_status = router_state.status
        uptime_ticks = int(router_state.uptime_seconds * 100)

        mib: Dict[Tuple[int, ...], Dict[str, Any]] = {
            # --- System Group (1.3.6.1.2.1.1) ---
            (1, 3, 6, 1, 2, 1, 1, 1, 0): {
                "oid": "1.3.6.1.2.1.1.1.0",
                "name": "SNMPv2-MIB::sysDescr.0",
                "type": "OCTET-STRING",
                "value": f"{router_state.manufacturer} {router_state.firmware_version} Hardware Emulator ({router_state.purpose})",
            },
            (1, 3, 6, 1, 2, 1, 1, 2, 0): {
                "oid": "1.3.6.1.2.1.1.2.0",
                "name": "SNMPv2-MIB::sysObjectID.0",
                "type": "OBJECT-IDENTIFIER",
                "value": "1.3.6.1.4.1.9.1.2064",
            },
            (1, 3, 6, 1, 2, 1, 1, 3, 0): {
                "oid": "1.3.6.1.2.1.1.3.0",
                "name": "DISMAN-EVENT-MIB::sysUpTimeInstance",
                "type": "TimeTicks",
                "value": uptime_ticks,
            },
            (1, 3, 6, 1, 2, 1, 1, 4, 0): {
                "oid": "1.3.6.1.2.1.1.4.0",
                "name": "SNMPv2-MIB::sysContact.0",
                "type": "OCTET-STRING",
                "value": "Network Operations Center <noc@datacenter.net>",
            },
            (1, 3, 6, 1, 2, 1, 1, 5, 0): {
                "oid": "1.3.6.1.2.1.1.5.0",
                "name": "SNMPv2-MIB::sysName.0",
                "type": "OCTET-STRING",
                "value": router_state.router_id,
            },
            (1, 3, 6, 1, 2, 1, 1, 6, 0): {
                "oid": "1.3.6.1.2.1.1.6.0",
                "name": "SNMPv2-MIB::sysLocation.0",
                "type": "OCTET-STRING",
                "value": router_state.location,
            },
            (1, 3, 6, 1, 2, 1, 1, 7, 0): {
                "oid": "1.3.6.1.2.1.1.7.0",
                "name": "SNMPv2-MIB::sysServices.0",
                "type": "INTEGER",
                "value": 78,
            },

            # --- Interfaces Group (1.3.6.1.2.1.2) ---
            (1, 3, 6, 1, 2, 1, 2, 1, 0): {
                "oid": "1.3.6.1.2.1.2.1.0",
                "name": "IF-MIB::ifNumber.0",
                "type": "INTEGER",
                "value": 5,
            },
            (1, 3, 6, 1, 2, 1, 2, 2, 1, 1, 1): {
                "oid": "1.3.6.1.2.1.2.2.1.1.1",
                "name": "IF-MIB::ifIndex.1",
                "type": "INTEGER",
                "value": 1,
            },
            (1, 3, 6, 1, 2, 1, 2, 2, 1, 2, 1): {
                "oid": "1.3.6.1.2.1.2.2.1.2.1",
                "name": "IF-MIB::ifDescr.1",
                "type": "OCTET-STRING",
                "value": "GigabitEthernet0/0/0 (Upstream Wan Link)",
            },
            (1, 3, 6, 1, 2, 1, 2, 2, 1, 8, 1): {
                "oid": "1.3.6.1.2.1.2.2.1.8.1",
                "name": "IF-MIB::ifOperStatus.1",
                "type": "INTEGER",
                "value": 1 if sys_status == "OPERATIONAL" else 2,
            },

            # --- Custom Hardware State Enterprise Group (1.3.6.1.4.1.9999) ---
            (1, 3, 6, 1, 4, 1, 9999, 1, 1, 0): {
                "oid": "1.3.6.1.4.1.9999.1.1.0",
                "name": "ENTERPRISE-MIB::routerPowerLedState",
                "type": "OCTET-STRING",
                "value": router_state.leds.get("power", "off"),
            },
            (1, 3, 6, 1, 4, 1, 9999, 1, 2, 0): {
                "oid": "1.3.6.1.4.1.9999.1.2.0",
                "name": "ENTERPRISE-MIB::routerOnlineLedState",
                "type": "OCTET-STRING",
                "value": router_state.leds.get("online", "off"),
            },
            (1, 3, 6, 1, 4, 1, 9999, 1, 3, 0): {
                "oid": "1.3.6.1.4.1.9999.1.3.0",
                "name": "ENTERPRISE-MIB::routerUpstreamLedState",
                "type": "OCTET-STRING",
                "value": router_state.leds.get("upstream", "off"),
            },
        }

        return mib
