"""Router Node Domain Model Class for Router Operations Dashboard.

Encapsulates metadata, access endpoints, control header configurations, and secret IDs
for individual emulated router nodes in the fleet.
"""

from typing import Any, Dict, Optional


class RouterNode:
    """Represents an individual emulated router node in the fleet registry.

    Attributes:
        id: Unique string identifier (e.g. 'RTR-CAN-EAST-01').
        name: Human-readable display name string.
        url: Downstream HTTP/HTTPS endpoint URL string.
        location: Datacenter location description string.
        purpose: Operational purpose description string.
        secret_id: GCP Secret Manager secret ID string.
        control_header: Custom authorization header name string (default: 'X-Control-Password').
        control_password: Pre-configured control password fallback string.
        source: Discovery origin tag string ('CLOUDRUN' or 'MANUAL').
    """

    def __init__(
        self,
        id: str,
        name: str,
        url: str,
        location: str = "Remote Datacenter",
        purpose: str = "Edge Core Router",
        manufacturer: str = "Cisco Systems",
        model: str = "Nexus 9300-EX",
        last_updated: str = "",
        last_deployed: str = "",
        revision: str = "",
        secret_id: Optional[str] = None,
        control_header: str = "X-Control-Password",
        control_password: str = "",
        source: str = "MANUAL",
    ) -> None:
        """Initializes a new RouterNode domain instance.

        Args:
            id: Unique router string identifier.
            name: Display name string.
            url: Access URL string.
            location: Physical location description.
            purpose: Operational purpose description.
            manufacturer: Equipment manufacturer string (e.g. Cisco Systems, Juniper).
            model: Hardware model identifier string (e.g. Nexus 9300-EX).
            last_updated: Last telemetry update timestamp string.
            last_deployed: Date and time of last Cloud Run container deployment.
            revision: Active Cloud Run container revision name string.
            secret_id: Secret Manager secret identifier.
            control_header: Custom HTTP header key for control auth.
            control_password: Fallback control authorization password string.
            source: Discovery origin tag ('CLOUDRUN' or 'MANUAL').

        Raises:
            ValueError: If 'id' or 'url' are empty strings.
        """
        if not id or not id.strip():
            raise ValueError("Router ID cannot be empty.")
        if not url or not url.strip():
            raise ValueError("Router URL cannot be empty.")

        self.id: str = id.strip()
        self.name: str = name.strip() if name else self.id
        self.url: str = url.strip().rstrip("/")
        self.location: str = location.strip() if location else "Remote Datacenter"
        self.purpose: str = purpose.strip() if purpose else "Edge Core Router"
        self.manufacturer: str = manufacturer.strip() if manufacturer else "Cisco Systems"
        self.model: str = model.strip() if model else "Nexus 9300-EX"
        self.last_updated: str = last_updated.strip()
        self.last_deployed: str = last_deployed.strip()
        self.revision: str = revision.strip()
        self.secret_id: Optional[str] = secret_id.strip() if secret_id else None
        self.control_header: str = control_header.strip() if control_header else "X-Control-Password"
        self.control_password: str = control_password.strip()
        self.source: str = source.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Serializes RouterNode instance into a standard JSON dictionary representation.

        Returns:
            Dictionary containing all public fields of the router node.
        """
        data: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "location": self.location,
            "purpose": self.purpose,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "last_updated": self.last_updated,
            "last_deployed": self.last_deployed,
            "revision": self.revision,
            "control_header": self.control_header,
            "source": self.source,
        }
        if self.secret_id:
            data["secret_id"] = self.secret_id
        if self.control_password:
            data["control_password"] = self.control_password
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RouterNode":
        """Constructs a RouterNode instance from a raw dictionary object.

        Args:
            data: Raw dictionary containing router parameters.

        Returns:
            Instantiated RouterNode object.

        Raises:
            KeyError: If missing required 'id' or 'url' fields.
        """
        router_id = data.get("id", "")
        url = data.get("url", "")
        name = data.get("name", router_id)
        location = data.get("location", "Remote Datacenter")
        purpose = data.get("purpose", "Edge Core Router")
        manufacturer = data.get("manufacturer", "Cisco Systems")
        model = data.get("model", "Nexus 9300-EX")
        last_updated = data.get("last_updated", "")
        last_deployed = data.get("last_deployed", "")
        revision = data.get("revision", "")
        secret_id = data.get("secret_id")
        control_header = data.get("control_header", "X-Control-Password")
        control_password = data.get("control_password", "")
        source = data.get("source", "MANUAL")

        return cls(
            id=router_id,
            name=name,
            url=url,
            location=location,
            purpose=purpose,
            manufacturer=manufacturer,
            model=model,
            last_updated=last_updated,
            last_deployed=last_deployed,
            revision=revision,
            secret_id=secret_id,
            control_header=control_header,
            control_password=control_password,
            source=source,
        )
