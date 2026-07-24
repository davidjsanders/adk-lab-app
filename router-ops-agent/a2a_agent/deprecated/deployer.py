import json
import logging
import os
from typing import Optional, Dict, Any
import vertexai
from vertexai import types
from google.cloud import resourcemanager_v3

logger = logging.getLogger(__name__)

class AgentEngineDeployer:
    """Handles end-to-end deployment of ADK agents to Vertex AI Agent Engine."""

    def __init__(
        self,
        project: str,
        location: str,
        staging_bucket: str,
        api_version: str = "v1beta1",
    ):
        """Initializes the deployer and configures Vertex AI clients."""
        self.project = project
        self.location = location
        self.staging_bucket = staging_bucket if staging_bucket.startswith("gs://") else f"gs://{staging_bucket}"

        logger.info("Initializing Vertex AI SDK...")
        vertexai.init(
            project=self.project,
            location=self.location,
            staging_bucket=self.staging_bucket,
        )

        logger.info("Initializing Vertex GenAI Client (%s)...", api_version)
        self.client = vertexai.Client(
            project=self.project,
            location=self.location,
            http_options=dict(api_version=api_version),
        )

    def deploy(
        self,
        agent: Any,
        display_name: str,
        requirements_path: str,
        agent_id: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        service_account: Optional[str] = None,
    ) -> str:
        """Executes the deploy transaction (create or update) and writes metadata."""
        # 2. Build config dictionary
        config = {
            "display_name": display_name,
            "requirements": requirements_path,
            "extra_packages": ["app", "a2a_agent"],
            "env_vars": env_vars if env_vars else None,
            "staging_bucket": self.staging_bucket,
        }

        # 3. Set secure Workload Identity type
        if service_account:
            config["service_account"] = service_account
            config["identity_type"] = types.IdentityType.SERVICE_ACCOUNT
        else:
            config["identity_type"] = types.IdentityType.AGENT_IDENTITY
            config["service_account"] = ""  # Explicitly clear service_account to transition existing resource state

        # 4. Trigger create or update transaction
        if agent_id:
            logger.info("Updating existing agent instance: %s", agent_id)
            resource_name = f"projects/{self.project}/locations/{self.location}/reasoningEngines/{agent_id}"
            remote_app = self.client.agent_engines.update(
                name=resource_name,
                agent=agent,
                config=config,
            )
        else:
            logger.info("Creating new agent instance...")
            remote_app = self.client.agent_engines.create(
                agent=agent,
                config=config,
            )

        resource_name = remote_app.api_resource.name
        logger.info("Successfully deployed! Resource name: %s", resource_name)

        # 4.5 Automatically grant required IAM roles to secure AGENT_IDENTITY
        if not service_account:
            try:
                self._grant_agent_identity_roles(agent_id=resource_name.split('/')[-1])
            except Exception as iam_exc:
                logger.error("Failed to automatically configure Agent Identity IAM roles: %s. Please configure them manually.", iam_exc, exc_info=True)

        # 5. Write metadata out to a JSON file
        self._write_metadata(remote_app)

        return resource_name

    def configure_iam_only(self, agent_id: str) -> None:
        """Public entry point to execute ONLY the AGENT_IDENTITY IAM role bindings, skipping deploy."""
        if not agent_id:
            raise ValueError("AGENT_ID must be provided/configured to run IAM-only configuration.")
        logger.info("Configuring IAM roles ONLY for Agent Engine instance: %s", agent_id)
        self._grant_agent_identity_roles(agent_id=agent_id)

    def _write_metadata(self, remote_app: Any) -> None:
        """Persists deployment details to deployment_metadata.json."""
        api_res = remote_app.api_resource
        create_time = getattr(api_res, "create_time", None)
        
        metadata = {
            "remote_agent_runtime_id": api_res.name,
            "remote_agent_engine_id": api_res.name,
            "deployment_target": "agent_runtime",
            "deployment_timestamp": create_time.isoformat() if create_time else None,
        }
        
        metadata_path = "deployment_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
            
        logger.info("Saved deployment metadata to %s", metadata_path)

    def _grant_agent_identity_roles(self, agent_id: str) -> None:
        """Automatically retrieves project IAM policy and grants all required roles to the AGENT_IDENTITY principal."""
        logger.info("Connecting to Resource Manager to resolve project parent and number...")
        rm_client = resourcemanager_v3.ProjectsClient()
        proj = rm_client.get_project(name=f"projects/{self.project}")
        project_number = proj.name.split('/')[-1]
        
        # Resolve parent organization ID recursively through folders
        parent = proj.parent
        folders_client = resourcemanager_v3.FoldersClient()
        while parent and not parent.startswith("organizations/"):
            if parent.startswith("folders/"):
                folder = folders_client.get_folder(name=parent)
                parent = folder.parent
            else:
                break
                
        if not parent or not parent.startswith("organizations/"):
            logger.warning("Could not resolve parent organization ID for project: %s (Parent: %s). Skipping dynamic IAM role binding.", self.project, proj.parent)
            return
            
        org_id = parent.split('/')[-1]
        
        # Construct secure Agent Identity principal name
        principal = f"principal://agents.global.org-{org_id}.system.id.goog/resources/aiplatform/projects/{project_number}/locations/{self.location}/reasoningEngines/{agent_id}"
        logger.info("Constructed Agent Identity Principal: %s", principal)
        
        # Define the required roles
        required_roles = [
            "roles/aiplatform.expressUser",
            "roles/serviceusage.serviceUsageConsumer",
            "roles/browser",
            "roles/cloudtrace.agent",
            "roles/logging.logWriter",
            "roles/secretmanager.secretAccessor",
            "roles/storage.objectAdmin",
            "roles/aiplatform.user",
        ]

        logger.info("Retrieving project IAM policy for project: %s...", self.project)
        policy = rm_client.get_iam_policy(resource=proj.name)
        
        policy_updated = False
        for role in required_roles:
            binding_found = False
            for binding in policy.bindings:
                if binding.role == role:
                    binding_found = True
                    if principal not in binding.members:
                        binding.members.append(principal)
                        policy_updated = True
                        logger.info("Added Agent Identity to existing role binding: %s", role)
                    break
                    
            if not binding_found:
                new_binding = policy.bindings.add()
                new_binding.role = role
                new_binding.members.append(principal)
                policy_updated = True
                logger.info("Created new role binding and added Agent Identity: %s", role)
                
        if policy_updated:
            logger.info("Committing updated project IAM policy to Google Cloud...")
            from google.iam.v1 import iam_policy_pb2
            request = iam_policy_pb2.SetIamPolicyRequest(
                resource=proj.name,
                policy=policy
            )
            rm_client.set_iam_policy(request=request)
            logger.info("Successfully configured secure AGENT_IDENTITY Workload Identity permissions!")
        else:
            logger.info("AGENT_IDENTITY principal already possesses all required IAM roles. Skipping policy updates.")
