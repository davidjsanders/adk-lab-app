"""MCP Toolset loader with dynamic Google Cloud identity authentication.

Loads MCP tools dynamically from the Cloud Run MCP server using McpToolset
and StreamableHTTPConnectionParams with an httpx_client_factory pre-bound via
functools.partial to refresh identity tokens for IAM-protected endpoints.
"""

import functools
import logging

import httpx
from google.adk.tools import BaseTool
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

from app.config import settings
from app.helpers.auth import build_proxy_headers

logger = logging.getLogger("router-agent.tools.mcp")


class DynamicAuth(httpx.Auth):
    """Dynamically injects fresh OIDC IAM headers into requests."""
    
    def __init__(self, target_url: str):
        self.target_url = target_url

    def auth_flow(self, request: httpx.Request):
        headers = build_proxy_headers(self.target_url)
        if "Authorization" in headers:
            request.headers["Authorization"] = headers["Authorization"]
        if "X-Serverless-Authorization" in headers:
            request.headers["X-Serverless-Authorization"] = headers["X-Serverless-Authorization"]
        yield request

# Create a shared transport for connection pooling
_SHARED_TRANSPORT = httpx.AsyncHTTPTransport(
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
)

def get_shared_transport() -> httpx.AsyncHTTPTransport:
    """Returns the shared httpx.AsyncHTTPTransport instance."""
    return _SHARED_TRANSPORT

def create_dynamic_httpx_client(target_url: str, **kwargs) -> httpx.AsyncClient:
    """Creates an AsyncClient sharing a pooled transport, with dynamic auth."""
    # Use shared transport for pooling
    kwargs["transport"] = _SHARED_TRANSPORT
    # Apply dynamic auth
    kwargs["auth"] = DynamicAuth(target_url)
    
    if "timeout" not in kwargs:
        kwargs["timeout"] = httpx.Timeout(30.0)
        
    return httpx.AsyncClient(**kwargs)



# Define partial factory binding base URL to guarantee origin-scoped IAM token generation
mcp_httpx_factory = functools.partial(
    create_dynamic_httpx_client, target_url=settings.mcp_server_url
)


# Initialize McpToolset with StreamableHTTPConnectionParams using dynamic client factory
mcp_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=f"{settings.mcp_server_url.rstrip('/')}/mcp",
        httpx_client_factory=mcp_httpx_factory,
    )
)


async def get_mcp_tools() -> list[BaseTool]:
    """Retrieves tools exposed by the remote MCP server.

    Returns:
        List of loaded ADK BaseTool objects.
    """
    try:
        tools = await mcp_toolset.get_tools()
        logger.info(
            f"Successfully loaded {len(tools)} tools from MCP server at {settings.mcp_server_url}"
        )
        return tools
    except Exception as err:
        logger.warning(
            f"Could not load MCP tools from {settings.mcp_server_url}: {err}"
        )
        return []
