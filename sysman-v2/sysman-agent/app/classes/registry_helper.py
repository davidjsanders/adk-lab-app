import logging
import os
from requests.exceptions import HTTPError

from google.adk.integrations.agent_registry import AgentRegistry
from google.auth import default

from ..models.registry_resource_type import RegistryResourceType


logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)

class RegistryHelper:
    def __init__(
        self,
        project_id: str,
        location: str,
    ) -> None:
        if not os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", None):
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
        self._location = location
        self._project_id = project_id

        self._registry = AgentRegistry(
            project_id=self._project_id,
            location=self._location,
        )

    @property
    def registry(self):
        return self._registry

    @property
    def location(self):
        return self._location

    @property
    def project_id(self):
        return self._project_id

    def find(self, display_name: str):
        pass

    def get(
        self,
        registered_name: str,
        resource_type: RegistryResourceType,
    ) -> Union[RemoteA2Agent]:
        match resource_type:
            case RegistryResourceType.AGENT:
                return self._get_agent(registered_name)
            case RegistryResourceType.MCP:
                return self._get_mcp(registered_name)
            case RegistryResourceType.ENDPOINT:
                pass
                # return self._get_endpoint(registered_name)
            case RegistryResourceType.SKILL:
                pass
                # return self._get_skill(registered_name)
            case _:
                raise ValueError(f"Unknown resource type: {resource_type}")

    def _get_agent(self, registered_name: str):
        logger.debug("Looking up agent: %s", registered_name)

        if registered_name.startswith("/projects"):
            registered_name = registered_name.split("/")[-1]

        _registered_name = (
            f"projects/{self.project_id}/"
            f"locations/{self.location}/"
            f"agents/{registered_name}"
        )

        try:
            logger.debug("Sending request")
            remote_agent = self.registry.get_remote_a2a_agent(
                agent_name=_registered_name
            )
            logger.debug("Retrieved agent: %s", _registered_name)
            return remote_agent
        except RuntimeError as e:
            print(f"Could not find: {_registered_name}")
            return None
        except HTTPError as e:
            if e.response.status_code == 404:
                print(f"Could not find: {_registered_name}")
                return None
        except Exception as e:
            print(f"Error: {e}")

    def _get_mcp(self, registered_name: str):
        logger.debug("Looking up mcp: %s", registered_name)

        if registered_name.startswith("/projects"):
            registered_name = registered_name.split("/")[-1]

        _registered_name = (
            f"projects/{self.project_id}/"
            f"locations/{self.location}/"
            f"mcpServers/{registered_name}"
        )

        try:
            logger.debug("Sending request")
            remote_mcp = self.registry.get_mcp_toolset(
                _registered_name
            )
            logger.debug("Retrieved mcp: %s", _registered_name)
            return remote_mcp
        except RuntimeError as e:
            print(f"Could not find: {_registered_name}")
            return None
        except HTTPError as e:
            if e.response.status_code == 404:
                print(f"Could not find: {_registered_name}")
                return None
        except Exception as e:
            print(f"Error: {e}")

    def _get_endpoint(self, registered_name: str):
        pass

    def _get_skill(self, registered_name: str):
        pass
