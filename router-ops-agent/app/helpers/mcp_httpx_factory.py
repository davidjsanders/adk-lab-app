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

"""Global HTTPX client factory for MCP server communication."""

import functools
from app.config import settings
from app.helpers.create_dynamic_httpx_client import create_dynamic_httpx_client

# Global, reusable factory pre-bound to the MCP Server URL
mcp_httpx_factory = functools.partial(
    create_dynamic_httpx_client, target_url=settings.mcp_server_url
)
