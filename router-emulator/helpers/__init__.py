"""Helpers package for Router Emulator Application.

Provides helper utilities for Secret Manager retrieval and request header authentication.
"""

from helpers.logger import CloudRunJsonFormatter, setup_json_logging
from helpers.secret_manager import (
    fetch_router_secret,
    get_effective_control_password,
    get_secret_id_for_router,
    verify_control_auth,
)

__all__ = [
    "CloudRunJsonFormatter",
    "setup_json_logging",
    "fetch_router_secret",
    "get_effective_control_password",
    "get_secret_id_for_router",
    "verify_control_auth",
]
