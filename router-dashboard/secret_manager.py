"""Secret Manager integration module for Router Dashboard & Emulators.

Handles secure generation, storage, and retrieval of control password UUIDs
via Google Cloud Secret Manager API.
"""

import logging
import os
import time
from typing import Dict, Optional, Tuple, Union
import uuid

try:
    from google.cloud import secretmanager
    from google.api_core.exceptions import AlreadyExists, NotFound
    HAS_SECRET_MANAGER = True
except ImportError:
    HAS_SECRET_MANAGER = False

logger = logging.getLogger(__name__)

# In-memory secret cache with TTL to optimize latency
_SECRET_CACHE: Dict[str, Tuple[str, float]] = {}
CACHE_TTL_SECONDS: float = 300.0  # 5 minutes cache TTL


def generate_control_uuid() -> str:
    """Generates a secure cryptographically random UUID4 string for router control auth.

    Returns:
        UUID4 hex string.
    """
    return str(uuid.uuid4())


def get_secret_id_for_router(router_id: str) -> str:
    """Derives a compliant Secret Manager secret ID string for a given router ID.

    Args:
        router_id: Unique router identifier string.

    Returns:
        Clean Secret ID string (e.g. router-secret-rtr-us-east-01).
    """
    clean_id = "".join(c.lower() if c.isalnum() else "-" for c in router_id)
    clean_id = "-".join(filter(None, clean_id.split("-")))
    if not clean_id or not clean_id[0].isalpha():
        clean_id = "rtr-" + clean_id
    return f"router-secret-{clean_id[:45]}"


def store_router_secret(project_id: str, secret_id: str, secret_value: str) -> Tuple[bool, str]:
    """Stores a router control UUID secret in GCP Secret Manager.

    Args:
        project_id: Google Cloud project ID string.
        secret_id: Target Secret Manager secret ID string.
        secret_value: Secret UUID/password string to store.

    Returns:
        Tuple of (success_boolean, message_or_version_name).
    """
    if not HAS_SECRET_MANAGER:
        return False, "google-cloud-secret-manager package is not installed."

    if not project_id:
        return False, "GCP Project ID is required for Secret Manager operations."

    try:
        client = secretmanager.SecretManagerServiceClient()
        parent = f"projects/{project_id}"

        # 1. Create secret container if it doesn't already exist
        try:
            client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {
                        "replication": {"automatic": {}},
                    },
                }
            )
            logger.info(f"Created Secret Manager container '{secret_id}' in project '{project_id}'")
        except AlreadyExists:
            logger.info(f"Secret Manager container '{secret_id}' already exists.")

        # 2. Add secret version containing secret_value payload
        secret_path = f"projects/{project_id}/secrets/{secret_id}"
        payload = secret_value.encode("UTF-8")
        version = client.add_secret_version(
            request={
                "parent": secret_path,
                "payload": {"data": payload},
            }
        )

        # Invalidate cache entry
        _SECRET_CACHE.pop(secret_id, None)

        logger.info(f"Added secret version '{version.name}' to Secret Manager.")
        return True, version.name
    except Exception as err:
        logger.error(f"Error storing secret '{secret_id}' in Secret Manager: {err}")
        return False, str(err)


def fetch_router_secret(
    project_id: str,
    secret_id: str,
    version_id: str = "latest",
    use_cache: bool = True,
) -> Optional[str]:
    """Retrieves a router control UUID payload from GCP Secret Manager with caching.

    Args:
        project_id: Google Cloud project ID string.
        secret_id: Secret Manager secret ID string.
        version_id: Secret version ID string (defaults to 'latest').
        use_cache: Whether to use in-memory TTL caching.

    Returns:
        Retrieved secret string payload, or None if fetching fails.
    """
    now = time.time()

    # Return cached value if valid
    if use_cache and secret_id in _SECRET_CACHE:
        cached_val, cached_time = _SECRET_CACHE[secret_id]
        if now - cached_time < CACHE_TTL_SECONDS:
            return cached_val

    if not HAS_SECRET_MANAGER or not project_id or not secret_id:
        return None

    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        secret_val = response.payload.data.decode("UTF-8").strip()

        # Cache retrieved value
        _SECRET_CACHE[secret_id] = (secret_val, now)
        return secret_val
    except Exception as err:
        logger.error(f"Failed accessing secret '{secret_id}' from Secret Manager: {err}")
        return None
