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

"""Helper function for building HTTP proxy headers with IAM bearer tokens."""

from app.helpers.get_oidc_id_token import get_oidc_id_token


def build_proxy_headers(
    target_url: str, extra_headers: dict[str, str] | None = None
) -> dict[str, str]:
    """Builds HTTP request headers including ADC/IMPERSONATE_SA OIDC identity authorization headers.

    Args:
        target_url: Target Cloud Run endpoint URL string.
        extra_headers: Optional dictionary of additional HTTP headers.

    Returns:
        Combined header dictionary containing Authorization & X-Serverless-Authorization headers.

    Raises:
        None.
    """
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if extra_headers:
        headers.update(extra_headers)

    token = get_oidc_id_token(target_url)
    if token:
        bearer = f"Bearer {token}"
        headers["Authorization"] = bearer
        headers["X-Serverless-Authorization"] = bearer

    return headers
