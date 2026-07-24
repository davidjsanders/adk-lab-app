import json
import logging
import os
from typing import Optional, Dict, Any

# import vertexai
from google.cloud import resourcemanager_v3
from google import genai
from google.genai import types as genai_types
from vertexai import types as vertexai_types
from vertexai.preview.reasoning_engines import A2aAgent, ReasoningEngine

from app.classes.settings import Settings
from a2a_agent.helpers.load_env_vars import load_env_vars
from a2a_agent.helpers.load_requirements import load_requirements
from a2a_agent.models.platform import Platform
from a2a_agent.models.agent_configuration import AgentConfiguration

from vertexai._genai import Client as AgentEngineClient
from vertexai._genai import types as genai_types

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)


class Deployer:
    """Handles end-to-end deployment of ADK agents to Vertex AI Agent Engine."""

    def __init__(
        self,
        *,
        configuration: AgentConfiguration,
    ):
        """Initializes the deployer and configures Vertex AI clients."""
        logger.setLevel(level=logging.DEBUG)
        logger.debug("Initializing deployer")

        self.configuration = configuration

        # logger.info("Initializing Vertex AI SDK...")
        # vertexai.init(
        #     project=self.configuration.project_id,
        #     location=self.configuration.location,
        #     staging_bucket=self.configuration.staging_bucket,
        # )

        logger.info(
            "Initializing GenAI Client (%s)...",
            self.configuration.api_version
        )
        self.client = AgentEngineClient(
            project=self.configuration.project_id,
            location=self.configuration.location,
            http_options={"api_version": self.configuration.api_version}
        )
        # self.client = genai.Client(
        #     vertexai=True,  # Tells the client to target enterprise Vertex AI infrastructure
        #     project=self.configuration.project_id,
        #     location=self.configuration.location,
        #     http_options=genai_types.HttpOptions(
        #         api_version=self.configuration.api_version
        #     )
        # )
        # self.client = vertexai.Client(
        #     project=self.configuration.project_id,
        #     location=self.configuration.location,
        #     http_options=dict(api_version=self.configuration.api_version),
        # )

    def execute(self):
        """
        Execute the deployment
        """
        logger.debug("Executing deployment")

        logger.info(
            "Loading requirements file: %s",
            self.configuration.requirements_path
        )
        requirements = load_requirements(
            requirements_path=self.configuration.requirements_path
        )

        logger.info(
            "Loading environment variables from: %s",
            self.configuration.env_path
        )
        env_vars = load_env_vars(
            env_file=self.configuration.env_path,
            exclude_list=[
                'GOOGLE_CLOUD_PROJECT',
                'GOOGLE_CLOUD_LOCATION',
                'IMPERSONATE_SA',
            ],
        )

        config = {
            "display_name": self.configuration.display_name,
            "requirements": requirements,
            "extra_packages": self.configuration.package_directories,
            "env_vars": env_vars,
            "staging_bucket": self.configuration.staging_bucket,
            "agent_framework": "google-adk",
        }

        if self.configuration.platform == Platform.GOOGLE_CLOUD_AGENT_ENGINE:
            self._execute_ae(config)

    def _execute_ae(self, config: Dict[str, Any]):
        """
        Execute the deployment to Vertex AI Agent Engine
        """
        logger.debug("Target is Agent Runtime (aka Agent Engine)")

        if self.configuration.service_account:
            config["service_account"] = self.configuration.service_account
            config["identity_type"] = "SERVICE_ACCOUNT"
        else:
            config["service_account"] = ""
            config["identity_type"] = "AGENT_IDENTITY"

        resource_id = self._lookup_ae_instance()

        logger.debug(
            "Deployment Config = %s",
            json.dumps(config, indent=2)
        )
        logger.debug(
            "Resource (if any): %s",
            resource_id
        )

        if resource_id:
            logger.debug(
                "Updating existing agent runtime: %s",
                resource_id
            )
            remote_app = self.client.agent_engines.update(
                name=resource_id,
                agent=self.configuration.agent,
                config=genai_types.AgentEngineConfig(
                    **config
                ),
            )
        else:
            logger.debug("Deploying to new instance")
            remote_app = self.client.agent_engines.create(
                agent=self.configuration.agent,
                config=genai_types.AgentEngineConfig(
                    **config
                ),
            )

        logger.info(
            "Successfully deployed! Resource name: %s",
            remote_app.api_resource.name
        )

    def _lookup_ae_instance(self) -> Optional[str]:
        """
        Look up an existing Agent Engine instance
        """
        if not self.configuration.agent_id:
            return None

        if not self.configuration.agent_id.startswith("projects/"):
            resource_name = (
                f"projects/{self.configuration.project_id}/"
                f"locations/{self.configuration.location}/"
                f"reasoningEngines/{self.configuration.agent_id}"
            )
        else:
            resource_name = self.configuration.agent_id

        logger.debug("Checking if %s exists", resource_name)
        try:
            remote_agent_runtime = ReasoningEngine(resource_name)
            return resource_name
        except Exception as e:
            logger.error("Failed to get agent runtime: %s", e)
            raise ValueError(
                f"Agent runtime {resource_name} does not exist"
            ) from e
