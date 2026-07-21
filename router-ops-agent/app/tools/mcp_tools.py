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

"""MCP Toolset configuration and initialization."""

from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

from app.config import settings
from app.helpers.mcp_httpx_factory import mcp_httpx_factory

# Initialize McpToolset with StreamableHTTPConnectionParams using global dynamic client factory
mcp_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=f"{settings.mcp_server_url.rstrip('/')}/mcp",
        httpx_client_factory=mcp_httpx_factory,
    )
)
