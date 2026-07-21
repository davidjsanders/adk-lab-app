# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Helper function for retrieving tools from an MCP toolset."""

import logging
from google.adk.tools import BaseTool
from google.adk.tools.mcp_tool import McpToolset

logger = logging.getLogger("router-ops-agent.helpers.get_mcp_tools")


async def get_mcp_tools(toolset: McpToolset) -> list[BaseTool]:
    """Retrieves tools exposed by the remote MCP server toolset.

    Args:
        toolset: The McpToolset instance to retrieve tools from.

    Returns:
        List of loaded ADK BaseTool objects.
    """
    try:
        tools = await toolset.get_tools()
        logger.info(f"Successfully loaded {len(tools)} tools from MCP server.")
        return tools
    except Exception as err:
        logger.warning(f"Could not load MCP tools from toolset: {err}")
        return []
