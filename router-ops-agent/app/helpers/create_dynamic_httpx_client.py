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

"""Helper factory function for creating dynamic authenticated HTTPX async clients."""

import httpx

from app.classes.dynamic_auth import DynamicAuth
from app.helpers.shared_transport import get_shared_transport


def create_dynamic_httpx_client(target_url: str, **kwargs) -> httpx.AsyncClient:
    """Creates an AsyncClient sharing a pooled transport, with dynamic auth.

    Args:
        target_url: Target base URL for the client.
        **kwargs: Additional keyword arguments passed to httpx.AsyncClient.

    Returns:
        Configured httpx.AsyncClient instance.
    """
    kwargs["transport"] = get_shared_transport()
    kwargs["auth"] = DynamicAuth(target_url)

    if "timeout" not in kwargs:
        kwargs["timeout"] = httpx.Timeout(30.0)

    return httpx.AsyncClient(**kwargs)
