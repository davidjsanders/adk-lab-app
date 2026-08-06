# Google Cloud Agent Identity 3-Legged OAuth Setup Guide (ADK 2.6.0+)

This guide explains how to set up **Three-Legged OAuth (3LO)** for tools or MCP servers in your Agent Development Kit (ADK) application using **Google Cloud Agent Identity** and **Agent Registry**. This allows your agent to execute authenticated actions on behalf of the end-user, prompting them for consent when needed.

---

## Prerequisites

*   **Google Cloud SDK** installed and updated (`gcloud components update`).
*   **google-adk[gcp,agent-identity]** version **2.6.0** or later.
*   Required APIs enabled in your Google Cloud Project:
    ```bash
    gcloud services enable agentidentity.googleapis.com agentregistry.googleapis.com
    ```

---

## Step 1: Create OAuth 2.0 Web Application Credentials

1.  In the Google Cloud Console, navigate to **APIs & Services** ➔ **Credentials**.
2.  Click **Create Credentials** ➔ **OAuth client ID**.
3.  Select **Web application** as the Application Type.
4.  Configure the **Authorized redirect URIs**:
    *   **CRITICAL (ADK 2.6.0+):** Add the standard Google Cloud IAM Connector callback URL:
        ```
        https://iamconnectorcredentials.googleapis.com/v1/projects/YOUR_PROJECT_ID/locations/YOUR_LOCATION/connectors/YOUR_CONNECTOR_NAME/oauthcallback
        ```
        *Replace `YOUR_PROJECT_ID`, `YOUR_LOCATION` (e.g. `us-central1`), and `YOUR_CONNECTOR_NAME` with your actual setup values.*
    *   *(Optional)* Add your frontend's redirect callback if running a custom production web client:
        ```
        https://your-domain.com/oauth-callback
        ```
5.  Click **Create** and save the **Client ID** and **Client Secret**.

---

## Step 2: Create the Agent Identity Auth Connector

Create the connector using the `gcloud alpha agent-identity connectors` command group:

```bash
gcloud alpha agent-identity connectors create "YOUR_CONNECTOR_NAME" \
  --project="YOUR_PROJECT_ID" \
  --location="YOUR_LOCATION" \
  --three-legged-oauth-client-id="YOUR_CLIENT_ID" \
  --three-legged-oauth-client-secret="YOUR_CLIENT_SECRET" \
  --three-legged-oauth-authorization-url="https://accounts.google.com/o/oauth2/v2/auth" \
  --three-legged-oauth-token-url="https://oauth2.googleapis.com/token" \
  --allowed-scopes="https://www.googleapis.com/auth/cloud-platform"
```

---

## Step 3: Configure IAM Access Permissions

To allow the agent runner (and you, during local testing) to query and retrieve credentials from this connector, grant the `roles/iamconnectors.user` role:

### 1. Grant to yourself (for local development)
```bash
gcloud alpha agent-identity connectors add-iam-policy-binding "YOUR_CONNECTOR_NAME" \
  --project="YOUR_PROJECT_ID" \
  --location="YOUR_LOCATION" \
  --role="roles/iamconnectors.user" \
  --member="user:YOUR_EMAIL@domain.com"
```

### 2. Grant to the agent's Service Account (for production)
```bash
gcloud alpha agent-identity connectors add-iam-policy-binding "YOUR_CONNECTOR_NAME" \
  --project="YOUR_PROJECT_ID" \
  --location="YOUR_LOCATION" \
  --role="roles/iamconnectors.user" \
  --member="serviceAccount:YOUR_AGENT_SERVICE_ACCOUNT@YOUR_PROJECT_ID.iam.gserviceaccount.com"
```

---

## Step 4: Register Auth Provider & Apply Monkey Patches in Agent Code

To work around known ADK bugs (pre-auth callback ID mismatch, transient replication delays, and A2A user ID finalization mismatch), you must configure your codebase with the following structure:

### 1. In `app/helpers/auth.py`:
Add the `patch_credential_manager()` and `patch_finalize_credentials()` helper functions to define the monkey-patches:

```python
def patch_credential_manager() -> None:
    """Patches CredentialManager to fix ADK pre-auth callback ID bug and handle GCP sync delay."""
    from google.adk.auth.credential_manager import CredentialManager
    import asyncio
    import logging

    logger = logging.getLogger("sysman-agent.agent")
    _orig_get_auth_credential = CredentialManager.get_auth_credential

    async def _patched_get_auth_credential(self, context):
        if context.function_call_id is None:
            # Resolve the ADK pre-auth callback ID mismatch
            context.function_call_id = "_adk_toolset_auth_AgentRegistrySingleMcpToolset"
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                res = await _orig_get_auth_credential(self, context)
                return res
            except RuntimeError as e:
                # Catch transient replication delays on the GCP backend and retry
                if "Failed to retrieve consent based credential" in str(e) and attempt < max_retries - 1:
                    logger.warning(
                        f"Credential retrieval failed (attempt {attempt+1}/{max_retries}). "
                        "GCP connector might be syncing. Retrying in 2 seconds..."
                    )
                    await asyncio.sleep(2)
                else:
                    raise e

    CredentialManager.get_auth_credential = _patched_get_auth_credential


def patch_finalize_credentials() -> None:
    """Patches IAMConnectorCredentialsServiceClient.finalize_credentials to log A2A finalization mismatches."""
    from google.cloud.iamconnectorcredentials_v1alpha import IAMConnectorCredentialsServiceClient
    import logging

    logger = logging.getLogger("sysman-agent.agent")
    _orig_finalize_credentials = IAMConnectorCredentialsServiceClient.finalize_credentials

    def _patched_finalize_credentials(self, request, *args, **kwargs):
        try:
            return _orig_finalize_credentials(self, request, *args, **kwargs)
        except Exception as e:
            msg = str(e)
            if "does not match the state user ID" in msg:
                logger.error(
                    "A2A User ID mismatch detected during finalization! "
                    f"Request User ID: '{request.user_id}'. "
                    "Ensure sub-agents have configured 'request_converter' to align user IDs."
                )
            raise e

    IAMConnectorCredentialsServiceClient.finalize_credentials = _patched_finalize_credentials
```

### 2. In your entry point file (`app/agent.py`):
Import and call both helpers:

```python
from google.adk.auth.credential_manager import CredentialManager
from google.adk.integrations.agent_identity import GcpAuthProvider
from .helpers.auth import patch_credential_manager, patch_finalize_credentials

# Register the GCP Auth Provider (Must be done once before initializing the App)
CredentialManager.register_auth_provider(GcpAuthProvider())

# Apply the monkey patches to work around ADK bugs
patch_credential_manager()
patch_finalize_credentials()
```

### 3. In `app/app_utils/a2a.py` (for sub-agents):
To align user IDs in local testing (sandbox), you must override the sub-agent's A2A request converter so that it maps incoming session calls to the default playground user `"user"` instead of dynamically generating `A2A_USER_<session_id>`.

Update `attach_a2a_routes` to configure `request_converter`:

```python
    from google.adk.a2a.converters.request_converter import convert_a2a_request_to_agent_run_request

    def _custom_request_converter(request, part_converter):
        run_req = convert_a2a_request_to_agent_run_request(request, part_converter)
        # Override dynamic A2A user ID with the playground's default user ID
        run_req.user_id = "user"
        return run_req

    executor_config = A2aAgentExecutorConfig(
        request_converter=_custom_request_converter,
        execute_interceptors=[
            a2ui_converter_interceptor,
        ]
    )
```

---

## Step 5: Configure the Redirect & Session Continuity URL

To prevent the local API server's static redirects from discarding OAuth verification state query parameters, you must configure your runtime environment variables to point directly to the static `index.html` file.

### Local Development (`.env` or environment script):
```bash
CONTINUE_URI=http://127.0.0.1:8080/dev-ui/index.html
```

---

## Step 6: Bind the Tool/Toolset in your Agent Configuration

Configure the tool or MCP Toolset with the `GcpAuthProviderScheme` pointing to your connector resource. If retrieving toolsets dynamically from the **Agent Registry**, the ADK will resolve the connection scheme automatically from the registry binding using the `continue_uri` setting:

```python
from google.adk.integrations.agent_identity import GcpAuthProviderScheme
from google.adk.tools.mcp import McpToolset

auth_scheme = GcpAuthProviderScheme(
    name="projects/YOUR_PROJECT_ID/locations/YOUR_LOCATION/connectors/YOUR_CONNECTOR_NAME",
    continue_uri="http://127.0.0.1:8080/dev-ui/index.html"  # Points directly to index.html
)
```

---

## Troubleshooting

### Loop / "Consent Required" showing continuously (FastAPI / Popup issues)
*   **Query parameters stripped in Dev UI redirect:** Make sure your `CONTINUE_URI` includes the trailing `index.html` (e.g. `http://127.0.0.1:8080/dev-ui/index.html`). If it points to `/dev-ui/`, FastAPI's default redirect routes may strip the `user_id_validation_state` before the browser app can process it.
*   **Pre-Authentication Callback Mismatch:** Verify that you have applied the `_patched_get_auth_credential` monkey-patch listed in Step 4. Without it, the ADK fails to recognize the user's completed consent during the pre-authorization pass and requests credentials repeatedly.
*   **Incorrect Redirect URI:** Double check that you registered `.../connectors/...` instead of `.../authProviders/...` in your Google Cloud Console OAuth Client settings.
