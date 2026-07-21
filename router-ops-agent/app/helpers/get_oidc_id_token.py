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

"""Helper function for generating Google Cloud OIDC ID tokens."""

import logging
import os
import time
from urllib.parse import urlparse

import google.auth
import google.auth.transport.requests
from google.auth.impersonated_credentials import Credentials, IDTokenCredentials
from google.oauth2 import id_token

logger = logging.getLogger("router-ops-agent.helpers.get_oidc_id_token")

# In-memory OIDC ID token cache indexed by audience URL
_OIDC_TOKEN_CACHE: dict[str, tuple[str, float]] = {}


def get_oidc_id_token(target_url: str) -> str | None:
    """Generates an OIDC ID token for Cloud Run IAM using IMPERSONATE_SA or default ADC.

    Args:
        target_url: Target Cloud Run service endpoint URL string.

    Returns:
        OIDC identity token string, or None if token generation fails.

    Raises:
        None.
    """
    if not target_url or not target_url.startswith("http"):
        return None

    if "127.0.0.1" in target_url or "localhost" in target_url:
        return None

    parsed = urlparse(target_url)
    audience = f"{parsed.scheme}://{parsed.netloc}"

    now = time.time()
    if audience in _OIDC_TOKEN_CACHE:
        token_str, exp_time = _OIDC_TOKEN_CACHE[audience]
        if now < exp_time - 60:
            return token_str

    auth_req = google.auth.transport.requests.Request()

    # 1. Impersonation path via Google Auth Python SDK (pure Python SDK, 0 subprocesses)
    impersonate_sa = os.getenv("IMPERSONATE_SA", "").strip()
    if impersonate_sa:
        try:
            base_credentials, _ = google.auth.default()
            impersonated_credentials = Credentials(
                source_credentials=base_credentials,
                target_principal=impersonate_sa,
                target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            target_id_credentials = IDTokenCredentials(
                target_credentials=impersonated_credentials,
                target_audience=audience,
                include_email=True,
            )
            target_id_credentials.refresh(auth_req)
            token = target_id_credentials.token
            if token:
                _OIDC_TOKEN_CACHE[audience] = (token, now + 3500)
                return token
        except Exception as gerr:
            logger.warning(
                f"Failed generating OIDC token via Python SDK impersonation ({impersonate_sa}) for {audience}: {gerr}"
            )

    # 2. Native runtime path: Use default ADC service account token generation (Cloud Run runtime)
    try:
        token = id_token.fetch_id_token(auth_req, audience)
        _OIDC_TOKEN_CACHE[audience] = (token, now + 3500)
        return token
    except Exception as err:
        logger.debug(
            f"Default ADC OIDC ID token creation for {audience} unavailable: {err}"
        )

    return None
