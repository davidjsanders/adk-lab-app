"""Client for communicating with SysMan emulator endpoints."""

import json
import logging
import os
from typing import Any, Dict, List, Optional
import requests

from models import SystemMetadata, SystemStatus, LogEntry

logger = logging.getLogger("sysman.emulator_client")


class EmulatorClient:
    """Encapsulates HTTP operations to query and control SysMan emulators."""

    def __init__(
        self,
        emulator_url: Optional[str] = None,
        control_header: Optional[str] = None,
        control_password: Optional[str] = None,
        system_emulators_json: Optional[str] = None,
    ) -> None:
        """Initializes client with connection and authentication settings.

        Args:
            emulator_url: Default emulator URL.
            control_header: HTTP Header key for control auth password.
            control_password: HTTP password token.
            system_emulators_json: JSON string mapping system IDs to custom URLs.
        """
        self.emulator_url = (
            emulator_url or os.getenv("EMULATOR_URL", "http://127.0.0.1:8081")
        ).rstrip("/")
        self.control_header = control_header or os.getenv("CONTROL_HEADER", "X-Control-Password")
        self.control_password = control_password or os.getenv("CONTROL_PASSWORD", "SysManSecretPass123!")
        
        # Load custom emulator mapping
        raw_emulators = system_emulators_json or os.getenv("SYSTEM_EMULATORS", "").strip()
        self.emulators_map: Dict[str, str] = {}
        if raw_emulators:
            try:
                parsed = json.loads(raw_emulators)
                self.emulators_map = {k: v.rstrip("/") for k, v in parsed.items()}
            except Exception as err:
                logger.error("Failed parsing SYSTEM_EMULATORS JSON config: %s", err)

    def _get_url_for_system(self, system_id: str) -> str:
        """Resolves target emulator base URL for a given system ID.

        Args:
            system_id: Unique string ID of the target system.

        Returns:
            Resolved emulator base URL.
        """
        return self.emulators_map.get(system_id, self.emulator_url)

    def _get_google_id_token(self, audience: str) -> Optional[str]:
        """Fetches a Google Cloud ID token for the specified audience."""
        try:
            import google.auth
            import google.auth.transport.requests
            from google.oauth2 import id_token

            credentials, project = google.auth.default()
            auth_req = google.auth.transport.requests.Request()
            return id_token.fetch_id_token(auth_req, audience)
        except Exception as err:
            logger.warning("Failed fetching Google ID token for audience '%s': %s", audience, err)
            return None

    def _get_headers(self, target_url: str, system_id: Optional[str] = None) -> Dict[str, str]:
        """Compiles headers for emulator request authentication, attaching ID tokens if cloud deployed.

        Args:
            target_url: The destination request endpoint URL.
            system_id: Target system ID to resolve dynamic credentials from Secret Manager.

        Returns:
            Dictionary of headers containing control and authentication tokens.
        """
        header_name = self.control_header
        password = self.control_password

        if system_id:
            secret_data = self._fetch_secret_credentials(system_id)
            if secret_data:
                header_name = secret_data.get("header", header_name)
                password = secret_data.get("password", password)

        headers = {
            "Content-Type": "application/json",
            header_name: password,
        }
        if ".run.app" in target_url:
            from urllib.parse import urlparse
            parsed = urlparse(target_url)
            audience = f"{parsed.scheme}://{parsed.netloc}"
            token = self._get_google_id_token(audience)
            if token:
                headers["Authorization"] = f"Bearer {token}"
        return headers

    def _fetch_secret_credentials(self, system_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves control password and header name configurations from Google Cloud Secret Manager.

        Args:
            system_id: The ID of the emulator node.

        Returns:
            Dictionary containing 'password' and 'header', or None if retrieval fails.
        """
        try:
            from google.cloud import secretmanager
            import google.auth

            credentials, project_id = google.auth.default()
            if not project_id:
                return None

            impersonated_sa = os.getenv("IMPERSONATE_SA")
            if impersonated_sa:
                from google.auth import impersonated_credentials
                creds = impersonated_credentials.Credentials(
                    source_credentials=credentials,
                    target_principal=impersonated_sa,
                    target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )
            else:
                creds = credentials

            client = secretmanager.SecretManagerServiceClient(credentials=creds)
            secret_id = f"sysman-emulator-{system_id}"
            name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"

            response = client.access_secret_version(request={"name": name})
            payload = response.payload.data.decode("UTF-8")
            return json.loads(payload)
        except Exception as err:
            logger.warning(
                "Failed fetching secret 'sysman-emulator-%s' from Secret Manager: %s. Using default env fallback.",
                system_id,
                err,
            )
            return None

    def list_systems(self) -> List[SystemMetadata]:
        """Lists all registered virtual systems in the fleet.

        Returns:
            List of SystemMetadata models representing system telemetry information.

        Raises:
            RuntimeError: If communicating with the emulator service fails.
        """
        if not self.emulators_map:
            # Fallback to single default emulator status endpoint
            url = f"{self.emulator_url}/api/status"
            try:
                headers = self._get_headers(url)
                resp = requests.get(url, headers=headers, timeout=5)
                resp.raise_for_status()
                data = resp.json()
                systems = data.get("systems", [])
                return [
                    SystemMetadata(
                        system_id=sys.get("system_id", sys.get("id")),
                        name=sys.get("name"),
                        type=sys.get("type", "linux"),
                        status=sys.get("status", "UNKNOWN"),
                    )
                    for sys in systems
                ]
            except Exception as err:
                logger.error("Failed querying active systems list from default emulator: %s", err)
                raise RuntimeError(
                    f"Failed querying active systems from emulator at {url}: {err}"
                ) from err

        # Query from multiple emulators in configuration map
        all_systems: List[SystemMetadata] = []
        for sys_id, base_url in self.emulators_map.items():
            url = f"{base_url}/api/status"
            try:
                headers = self._get_headers(url, system_id=sys_id)
                resp = requests.get(url, headers=headers, params={"system_id": sys_id}, timeout=3)
                if resp.status_code == 200:
                    sys_data = resp.json()
                    all_systems.append(
                        SystemMetadata(
                            system_id=sys_data.get("system_id", sys_id),
                            name=sys_data.get("name", sys_id),
                            type=sys_data.get("type", "linux"),
                            status=sys_data.get("status", "UNKNOWN"),
                        )
                    )
            except Exception as err:
                logger.warning("Failed querying emulator at %s for system %s: %s", url, sys_id, err)
                all_systems.append(
                    SystemMetadata(
                        system_id=sys_id,
                        name=sys_id,
                        type="unknown",
                        status="UNKNOWN",
                    )
                )
        return all_systems

    def get_system_status(self, system_id: str) -> SystemStatus:
        """Queries detailed status, metrics, and health of a specific system.

        Args:
            system_id: Unique string ID of the target system.

        Returns:
            SystemStatus Pydantic model.

        Raises:
            RuntimeError: If status query fails.
        """
        base_url = self._get_url_for_system(system_id)
        url = f"{base_url}/api/status"
        try:
            headers = self._get_headers(url, system_id=system_id)
            resp = requests.get(url, headers=headers, params={"system_id": system_id}, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            return SystemStatus.model_validate(data)
        except Exception as err:
            logger.error("Failed fetching status for system '%s': %s", system_id, err)
            raise RuntimeError(f"Failed fetching status for '{system_id}' at {url}: {err}") from err

    def execute_system_command(self, system_id: str, command: str) -> Dict[str, Any]:
        """Sends control operations to the target system.

        Args:
            system_id: Target system ID.
            command: Command keyword to execute.

        Returns:
            Dictionary containing execution result status and message.

        Raises:
            RuntimeError: If command execution request fails.
        """
        base_url = self._get_url_for_system(system_id)
        url = f"{base_url}/api/command"
        payload = {"system_id": system_id, "command": command}
        try:
            headers = self._get_headers(url, system_id=system_id)
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as err:
            logger.error("Failed executing command '%s' on '%s': %s", command, system_id, err)
            raise RuntimeError(
                f"Failed executing command '{command}' on '{system_id}' at {url}: {err}"
            ) from err

    def get_system_logs(self, system_id: str, limit: int = 15) -> List[LogEntry]:
        """Retrieves recent syslog or application logs for the requested system.

        Args:
            system_id: Target system ID.
            limit: Number of recent log lines to retrieve (default: 15).

        Returns:
            List of LogEntry model objects.

        Raises:
            RuntimeError: If log query fails.
        """
        base_url = self._get_url_for_system(system_id)
        url = f"{base_url}/api/logs"
        try:
            headers = self._get_headers(url, system_id=system_id)
            resp = requests.get(url, headers=headers, params={"system_id": system_id, "limit": limit}, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            raw_logs = data.get("logs", [])
            return [LogEntry.model_validate(log) for log in raw_logs]
        except Exception as err:
            logger.error("Failed querying logs for system '%s': %s", system_id, err)
            raise RuntimeError(f"Failed querying logs for '{system_id}' at {url}: {err}") from err
