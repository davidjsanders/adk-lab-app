"""Helpers package for Router Operations Dashboard Application.

Provides helper modules for OIDC token authentication, Cloud Run CLI service operations,
and Secret Manager key management.
"""

from helpers.auth import build_proxy_headers, get_oidc_id_token
from helpers.cloud_run import deploy_router_to_cloud_run, discover_cloud_run_routers, sanitize_service_name
from helpers.secret_manager import (
    fetch_router_secret,
    generate_control_uuid,
    get_secret_id_for_router,
    store_router_secret,
)

__all__ = [
    "build_proxy_headers",
    "deploy_router_to_cloud_run",
    "discover_cloud_run_routers",
    "fetch_router_secret",
    "generate_control_uuid",
    "get_oidc_id_token",
    "get_secret_id_for_router",
    "sanitize_service_name",
    "store_router_secret",
]
