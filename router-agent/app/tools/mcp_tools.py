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

from app.config import MCP_SERVER_URL
from app.helpers import build_proxy_headers

logger = logging.getLogger("router-agent.tools.mcp")


def create_dynamic_httpx_client(target_url: str, **kwargs) -> httpx.AsyncClient:
    """Dynamic httpx client factory that injects fresh OIDC IAM headers on connection creation.

    Args:
        target_url: Target endpoint base URL string.
        **kwargs: Additional options for httpx.AsyncClient initialization.

    Returns:
        Configured httpx.AsyncClient instance.

    Raises:
        None.
    """
    headers = build_proxy_headers(target_url)
    if kwargs.get("headers"):
        headers.update(kwargs["headers"])
    timeout = kwargs.get("timeout", httpx.Timeout(30.0))
    return httpx.AsyncClient(headers=headers, timeout=timeout)


# Define partial factory binding base URL to guarantee origin-scoped IAM token generation
mcp_httpx_factory = functools.partial(
    create_dynamic_httpx_client, target_url=MCP_SERVER_URL
)

# Initialize McpToolset with StreamableHTTPConnectionParams using dynamic client factory
mcp_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=f"{MCP_SERVER_URL.rstrip('/')}/mcp",
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
            f"Successfully loaded {len(tools)} tools from MCP server at {MCP_SERVER_URL}"
        )
        return tools
    except Exception as err:
        logger.warning(f"Could not load MCP tools from {MCP_SERVER_URL}: {err}")
        return []
