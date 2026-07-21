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

"""Shared HTTPX transport module for connection pooling."""

import httpx

_SHARED_TRANSPORT = httpx.AsyncHTTPTransport(
    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
)


def get_shared_transport() -> httpx.AsyncHTTPTransport:
    """Returns the shared httpx.AsyncHTTPTransport instance.

    Returns:
        The singleton AsyncHTTPTransport instance configured for connection pooling.
    """
    return _SHARED_TRANSPORT
