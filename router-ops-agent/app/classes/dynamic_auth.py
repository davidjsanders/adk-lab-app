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

"""Dynamic authentication class for HTTPX requests."""

import httpx

from app.helpers.build_proxy_headers import build_proxy_headers


class DynamicAuth(httpx.Auth):
    """Dynamically injects fresh OIDC IAM headers into HTTP requests."""

    def __init__(self, target_url: str):
        """Initializes DynamicAuth with the target service URL.

        Args:
            target_url: The target endpoint URL string.
        """
        self.target_url = target_url

    def auth_flow(self, request: httpx.Request):
        """Yields request with injected authorization headers.

        Args:
            request: The outgoing HTTPX request object.

        Yields:
            The modified HTTPX request with Bearer authorization headers.
        """
        headers = build_proxy_headers(self.target_url)
        if "Authorization" in headers:
            request.headers["Authorization"] = headers["Authorization"]
        if "X-Serverless-Authorization" in headers:
            request.headers["X-Serverless-Authorization"] = headers[
                "X-Serverless-Authorization"
            ]
        yield request
