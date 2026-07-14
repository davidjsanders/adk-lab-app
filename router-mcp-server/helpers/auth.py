"""Authentication helpers for GCP Cloud Run IAM and IAP token generation."""

import logging
import os
import subprocess
from typing import Any, Dict, Optional
import urllib.parse

import google.auth
from google.auth.transport.requests import Request
from google.oauth2 import id_token
import requests

from .logger import setup_json_logging

logger = setup_json_logging("router-mcp-server.auth")

CONTROL_PASSWORD = os.getenv("ROUTER_CONTROL_PASSWORD", "mock-control-secret-key-12345")


def discover_iap_client_id(target_url: str) -> Optional[str]:
    """Programmatically extracts the IAP OAuth Client ID by parsing the 302 redirect location header.

    Args:
        target_url: Target Cloud Run service endpoint URL.

    Returns:
        Discovered IAP OAuth Client ID string, or None if discovery fails or target lacks IAP.

    Raises:
        None.
    """
    try:
        res = requests.get(target_url, allow_redirects=False, timeout=3)
        if res.status_code in (301, 302) and "Location" in res.headers:
            loc = res.headers["Location"]
            parsed_loc = urllib.parse.urlparse(loc)
            query_params = urllib.parse.parse_qs(parsed_loc.query)
            client_ids = query_params.get("client_id")
            if client_ids:
                return client_ids[0]
    except Exception as err:
        logger.debug(f"Failed auto-discovering IAP Client ID for {target_url}: {err}")
    return None


def get_oidc_id_token(target_url: str) -> Optional[str]:
    """Generates a fresh OIDC ID token for Cloud Run IAM on every call using IMPERSONATE_SA or default ADC.

    Args:
        target_url: Target Cloud Run service endpoint URL.

    Returns:
        Fresh OIDC identity token string, or None if token generation fails.

    Raises:
        None.
    """
    if not target_url or not target_url.startswith("http"):
        return None

    parsed = urllib.parse.urlparse(target_url)
    if parsed.hostname in ("127.0.0.1", "localhost"):
        return None

    iap_client_id = os.getenv("IAP_CLIENT_ID", "").strip()
    if not iap_client_id:
        iap_client_id = discover_iap_client_id(target_url)

    is_iap_target = bool(iap_client_id)
    audience = iap_client_id if iap_client_id else f"{parsed.scheme}://{parsed.netloc}"

    # 1. Impersonation path if IMPERSONATE_SA is set or default service account
    impersonate_sa = os.getenv("IMPERSONATE_SA", "router-dashboard-sa@agentspace-argolis-demo.iam.gserviceaccount.com").strip()
    if impersonate_sa:
        try:
            cmd = ["gcloud", "auth", "print-identity-token", f"--impersonate-service-account={impersonate_sa}", f"--audiences={audience}"]
            if is_iap_target:
                cmd.append("--include-email")
            logger.info(f"Generating OIDC token using IMPERSONATE_SA='{impersonate_sa}' for audience='{audience}' (IAP={is_iap_target})")
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            if res.returncode == 0:
                token_lines = [l.strip() for l in res.stdout.splitlines() if l.strip().startswith("eyJ")]
                if token_lines:
                    return token_lines[0]
        except Exception as gerr:
            logger.warning(f"Failed generating OIDC token via IMPERSONATE_SA ({impersonate_sa}) for {audience}: {gerr}")

    # 2. Native runtime path: Use default ADC service account token generation
    try:
        auth_req = Request()
        return id_token.fetch_id_token(auth_req, audience)
    except Exception as err:
        logger.debug(f"Default ADC OIDC ID token creation for {audience} unavailable: {err}")

    return None


def get_auth_headers(target_url: str) -> Dict[str, str]:
    """Generates authentication headers, injecting GCP OIDC ID token for Cloud Run targets.

    Args:
        target_url: Destination endpoint URL.

    Returns:
        Dictionary of HTTP request headers.

    Raises:
        None.
    """
    headers = {
        "Content-Type": "application/json",
        "X-Control-Password": CONTROL_PASSWORD,
    }

    token = get_oidc_id_token(target_url)
    if token:
        bearer = f"Bearer {token}"
        headers["Authorization"] = bearer
        headers["X-Serverless-Authorization"] = bearer

    return headers


def get_effective_control_password(node: Dict[str, Any]) -> str:
    """Resolves control authorization password from node dict, GCP Secret Manager, or environment fallback.

    Args:
        node: Target router node metadata dictionary.

    Returns:
        Active control password string.

    Raises:
        None.
    """
    if node.get("control_password"):
        return node["control_password"]

    secret_id = node.get("secret_id")
    if secret_id:
        try:
            import base64
            creds, _ = google.auth.default()
            req = Request()
            creds.refresh(req)
            sm_url = f"https://secretmanager.googleapis.com/v1/projects/63466983700/secrets/{secret_id}/versions/latest:access"
            sm_headers = {"Authorization": f"Bearer {creds.token}"}
            r_sm = requests.get(sm_url, headers=sm_headers, timeout=5)
            if r_sm.status_code == 200:
                payload_b64 = r_sm.json()["payload"]["data"]
                return base64.b64decode(payload_b64).decode("utf-8").strip()
        except Exception as err:
            logger.warning(f"Failed resolving secret '{secret_id}' from Secret Manager: {err}")

    return CONTROL_PASSWORD
