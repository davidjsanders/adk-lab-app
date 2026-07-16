"""Authentication Helper Module for Router Operations Dashboard Application.

Generates OpenID Connect (OIDC) ID tokens via IMPERSONATE_SA or Application Default
Credentials (ADC) to authorize service-to-service calls to IAM-protected Cloud Run instances.
"""

import logging
import os

import time
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

import google.auth
import google.auth.transport.requests
from google.auth import impersonated_credentials
from google.oauth2 import id_token

from .logger import setup_json_logging

logger = setup_json_logging("router-dashboard.auth")

# In-memory OIDC ID token cache indexed by audience URL
_OIDC_TOKEN_CACHE: Dict[str, Tuple[str, float]] = {}
IMPERSONATE_SA: str = os.getenv("IMPERSONATE_SA", "").strip()


def get_oidc_id_token(target_url: str) -> Optional[str]:
    """Generates an OIDC ID token for Cloud Run IAM using IMPERSONATE_SA or default ADC credentials.

    Args:
        target_url: Target Cloud Run service endpoint URL.

    Returns:
        OIDC identity token string, or None if token generation fails.
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

    # 1. Impersonation path using SDK if IMPERSONATE_SA is set in environment (workaround for internal Google workstations)
    impersonate_sa = os.getenv("IMPERSONATE_SA", "").strip()
    if impersonate_sa:
        try:
            source_creds, _ = google.auth.default()
            
            target_creds = impersonated_credentials.IDTokenCredentials(
                source_credentials=source_creds,
                target_principal=impersonate_sa,
                target_audience=audience,
                include_email=True # Assuming IAP might be involved or email is needed
            )
            
            auth_req = google.auth.transport.requests.Request()
            target_creds.refresh(auth_req)
            if target_creds.token:
                _OIDC_TOKEN_CACHE[audience] = (target_creds.token, now + 3500)
                return target_creds.token
        except Exception as gerr:
            logger.warning(f"Failed generating OIDC token via IMPERSONATE_SA SDK ({impersonate_sa}) for {audience}: {gerr}")

    # 2. Native runtime path: Use default ADC service account token generation (Cloud Run runtime)
    try:
        auth_req = google.auth.transport.requests.Request()
        token = id_token.fetch_id_token(auth_req, audience)
        _OIDC_TOKEN_CACHE[audience] = (token, now + 3500)
        return token
    except Exception as err:
        logger.debug(f"Default ADC OIDC ID token creation for {audience} unavailable: {err}")

    return None


def build_proxy_headers(target_url: str, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Builds HTTP request headers including ADC OIDC identity authorization headers.

    Args:
        target_url: Target Cloud Run endpoint URL string.
        extra_headers: Optional dictionary of additional HTTP headers.

    Returns:
        Combined header dictionary containing Authorization & X-Serverless-Authorization headers.
    """
    headers: Dict[str, str] = {}
    if extra_headers:
        headers.update(extra_headers)

    token = get_oidc_id_token(target_url)
    if token:
        bearer = f"Bearer {token}"
        headers["Authorization"] = bearer
        headers["X-Serverless-Authorization"] = bearer

    return headers
