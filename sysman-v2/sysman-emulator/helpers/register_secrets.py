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

"""Helper function to register system credentials with GCP Secret Manager."""

import json
import logging
import os
from typing import Dict, List
import uuid

logger = logging.getLogger("sysman-emulator.helpers.register_secrets")


def register_secrets_to_secret_manager(
    system_ids: List[str],
    control_password: str,
    control_header: str,
) -> Dict[str, str]:
    """Generates UUID passwords for all system IDs and registers them to GCP Secret Manager.

    Falls back to control_password if Secret Manager operations fail.

    Args:
        system_ids: List of system ID strings to register.
        control_password: Fallback control password.
        control_header: Control authorization HTTP header name.

    Returns:
        Dictionary mapping system ID to resolved control password.
    """
    control_passwords: Dict[str, str] = {}
    
    # Pre-populate fallback values
    for sys_id in system_ids:
        control_passwords[sys_id] = control_password

    try:
        # Lazy imports to prevent failures in environments where client library isn't configured
        from google.cloud import secretmanager
        import google.auth

        credentials, project_id = google.auth.default()
        if not project_id:
            logger.info("GCP Project ID not found. Using default environment CONTROL_PASSWORD.")
            return control_passwords

        impersonated_sa = os.getenv("IMPERSONATE_SA")
        if impersonated_sa:
            from google.auth import impersonated_credentials
            creds = impersonated_credentials.Credentials(
                source_credentials=credentials,
                target_principal=impersonated_sa,
                target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
            logger.info("Impersonating service account: %s", impersonated_sa)
        else:
            creds = credentials

        client = secretmanager.SecretManagerServiceClient(credentials=creds)
        parent = f"projects/{project_id}"

        for sys_id in system_ids:
            new_password = str(uuid.uuid4())
            secret_id = f"sysman-emulator-{sys_id}"
            secret_path = f"{parent}/secrets/{secret_id}"

            payload = {
                "system_id": sys_id,
                "password": new_password,
                "header": control_header
            }
            payload_bytes = json.dumps(payload).encode("UTF-8")

            # Try to create the secret
            try:
                client.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": secret_id,
                        "secret": {"replication": {"automatic": {}}}
                    }
                )
                logger.info("Created secret '%s' in Secret Manager.", secret_id)
            except Exception:
                # Secret already exists, ignore exception
                pass

            # Add secret version
            client.add_secret_version(
                request={
                    "parent": secret_path,
                    "payload": {"data": payload_bytes}
                }
            )
            control_passwords[sys_id] = new_password
            logger.info("Registered new control password version for system '%s' in Secret Manager.", sys_id)

    except Exception as err:
        logger.warning(
            "Failed writing passwords to GCP Secret Manager: %s. Using default env fallback.",
            err,
        )

    return control_passwords
