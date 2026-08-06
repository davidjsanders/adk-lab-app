import google.auth
from google.auth.transport.requests import Request
from google.oauth2 import id_token
import httpx
from urllib.parse import urlparse


class GoogleCloudRunAuth(httpx.Auth):
    """Auth class for fetching Google ID tokens for Cloud Run audiences."""
    def __init__(self, audience: str):
        self.audience = audience
        self._auth_req = Request()

    def auth_flow(self, request: httpx.Request):
        # Dynamically fetch ID token for Cloud Run target
        token = id_token.fetch_id_token(self._auth_req, self.audience)
        request.headers["Authorization"] = f"Bearer {token}"
        yield request


def get_authenticated_client(service_url: str, timeout: httpx.Timeout | None = None) -> httpx.AsyncClient:
    """Returns an httpx.AsyncClient pre-configured with Google ID token auth for Cloud Run."""
    parsed = urlparse(service_url)
    audience = f"{parsed.scheme}://{parsed.hostname}"
    resolved_timeout = timeout or httpx.Timeout(120.0)

    if "127.0.0.1" in audience or "localhost" in audience:
        return httpx.AsyncClient(timeout=resolved_timeout)
    return httpx.AsyncClient(
        auth=GoogleCloudRunAuth(audience),
        timeout=resolved_timeout
    )

def patch_credential_manager() -> None:
    """Patches CredentialManager to fix ADK pre-auth callback ID bug and handle GCP sync delay."""
    from google.adk.auth.credential_manager import CredentialManager
    import asyncio
    import logging

    logger = logging.getLogger("sysman-agent.agent")
    _orig_get_auth_credential = CredentialManager.get_auth_credential

    async def _patched_get_auth_credential(self, context):
        if context.function_call_id is None:
            context.function_call_id = "_adk_toolset_auth_AgentRegistrySingleMcpToolset"
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info("CredentialManager retrieving credentials for user_id: %s (function_call_id: %s)", getattr(context, "user_id", None), context.function_call_id)
                res = await _orig_get_auth_credential(self, context)
                return res
            except RuntimeError as e:
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



