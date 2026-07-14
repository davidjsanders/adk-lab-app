"""Cloud Run Service Management & Discovery Helper Module for Router Dashboard.

Handles pre-built image container deployments via `gcloud beta run deploy`
and auto-discovers active Cloud Run services starting with the `router-emulator-` prefix.
"""

import json
import logging
import os
import re
import google.auth
import google.auth.transport.requests
import requests
from typing import Any, Dict, List, Optional, Tuple

try:
    from google.cloud import secretmanager
except ImportError:
    secretmanager = None

from .logger import setup_json_logging
from .secret_manager import get_secret_id_for_router, store_router_secret

logger = setup_json_logging("router-dashboard.cloud_run")

# Environment defaults
DEFAULT_IMAGE_NAME: str = "us-central1-docker.pkg.dev/agentspace-argolis-demo/docker-registry/router-emulator:latest"


def sanitize_service_name(router_id: str) -> str:
    """Sanitizes a router ID string into a valid Cloud Run service name.

    Cloud Run service names must consist of lower case letters, numbers, and hyphens.

    Args:
        router_id: Unique string identifier for the router node.

    Returns:
        Sanitized Cloud Run service name string (e.g. 'router-emulator-rtr-can-east-01').
    """
    clean_id = re.sub(r"[^a-z0-9-]", "-", router_id.lower())
    clean_id = re.sub(r"-+", "-", clean_id).strip("-")

    if not clean_id.startswith("router-emulator-"):
        return f"router-emulator-{clean_id}"
    return clean_id


def discover_cloud_run_routers(project_id: str = "", region: str = "us-central1") -> List[Dict[str, Any]]:
    """Auto-discovers active Cloud Run router services matching the 'router-emulator-' prefix.

    Args:
        project_id: Google Cloud project ID string.
        region: Google Cloud region string.

    Returns:
        List of router dictionary records discovered from active Cloud Run instances.
    """
    project = project_id or os.getenv("GCP_PROJECT", "agentspace-argolis-demo")
    reg = region or os.getenv("GCP_REGION", "us-central1")

    try:
        credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)

        headers = {"Authorization": f"Bearer {credentials.token}"}
        api_url = f"https://run.googleapis.com/v1/projects/{project}/locations/{reg}/services"

        resp = requests.get(api_url, headers=headers, timeout=10)
        if not resp.ok:
            logger.warning(f"Cloud Run API discovery returned status {resp.status_code}: {resp.text}")
            return []

        data = resp.json()
        services = data.get("items", [])

        discovered: List[Dict[str, Any]] = []
        for svc in services:
            metadata = svc.get("metadata", {})
            name = metadata.get("name", "")
            if not name.startswith("router-emulator-"):
                continue

            status = svc.get("status", {})
            url = status.get("url", "")
            if not url:
                continue

            # Extract environment variables passed during deployment
            containers = svc.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
            env_vars: Dict[str, str] = {}
            if containers:
                for env_item in containers[0].get("env", []):
                    if "name" in env_item and "value" in env_item:
                        env_vars[env_item["name"]] = env_item["value"]

            # Reverse sanitize or extract router ID
            raw_router_id = env_vars.get("ROUTER_ID", "")
            if not raw_router_id:
                raw_router_id = name.replace("router-emulator-", "").upper()

            display_name = env_vars.get("ROUTER_NAME") or env_vars.get("NAME") or f"Cloud Run {raw_router_id}"
            location = env_vars.get("ROUTER_LOCATION", "GCP Cloud Run")
            purpose = env_vars.get("ROUTER_PURPOSE", "Emulated Router Node")
            secret_id = env_vars.get("CONTROL_SECRET_ID", get_secret_id_for_router(raw_router_id))
            revision = status.get("latestReadyRevisionName") or status.get("latestCreatedRevisionName", "")

            # Extract deployment timestamp (Ready / RoutesReady condition transition time or metadata creationTimestamp)
            last_deployed = ""
            for cond in status.get("conditions", []):
                if cond.get("type") in ("Ready", "RoutesReady", "ConfigurationsReady") and cond.get("lastTransitionTime"):
                    last_deployed = cond["lastTransitionTime"]
                    break
            if not last_deployed:
                last_deployed = metadata.get("creationTimestamp", "")

            discovered.append({
                "id": raw_router_id,
                "name": display_name,
                "url": url,
                "location": location,
                "purpose": purpose,
                "secret_id": secret_id,
                "revision": revision,
                "last_deployed": last_deployed,
                "control_header": env_vars.get("CONTROL_HEADER", "X-Control-Password"),
                "source": "CLOUDRUN",
            })

        logger.info(f"Auto-discovered {len(discovered)} Cloud Run router services in {project}/{reg}")
        return discovered
    except Exception as err:
        logger.warning(f"Failed discovering Cloud Run services: {err}")
        return []


def deploy_router_to_cloud_run(
    router_id: str,
    name: str = "",
    location: str = "",
    purpose: str = "",
    control_password: str = "",
    control_header: str = "X-Control-Password",
) -> Tuple[bool, str, str]:
    """Deploys a pre-built container image to Google Cloud Run for an emulated router instance.

    Args:
        router_id: Unique string identifier for the router node.
        name: Human-readable display name string.
        location: Operational datacenter location description.
        purpose: Hardware role purpose description.
        control_password: Pre-configured control authorization secret payload (generated if empty).
        control_header: Custom authorization header name string (default: 'X-Control-Password').

    Returns:
        Tuple of (success_boolean, service_url_or_error_message, revision_name).
    """
    project = os.getenv("GCP_PROJECT", "agentspace-argolis-demo")
    region = os.getenv("GCP_REGION", "us-central1")
    image = os.getenv("ROUTER_EMULATOR_IMAGE", DEFAULT_IMAGE_NAME)

    service_name = sanitize_service_name(router_id)
    secret_id = get_secret_id_for_router(router_id)

    # Auto-generate control password if not supplied
    if not control_password:
        from .secret_manager import generate_control_uuid
        control_password = generate_control_uuid()

    # Ensure secret is stored in Secret Manager before binding to Cloud Run
    sec_created, sec_msg = store_router_secret(project, secret_id, control_password)
    if not sec_created:
        logger.error(f"Secret Manager provisioning failed for '{secret_id}': {sec_msg}")
        return False, f"Secret Manager payload storage failed for '{secret_id}': {sec_msg}", ""

    try:
        credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)

        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        }

        import time

        service_body = {
            "apiVersion": "serving.knative.dev/v1",
            "kind": "Service",
            "metadata": {
                "name": service_name,
                "namespace": project,
            },
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "client.knative.dev/user-image": image,
                            "deployment.cloud.run/redeployed-at": str(time.time()),
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "image": image,
                                "resources": {
                                    "limits": {
                                        "memory": "2Gi",
                                        "cpu": "1000m",
                                    }
                                },
                                "env": [
                                    {"name": "ROUTER_ID", "value": router_id},
                                    {"name": "ROUTER_NAME", "value": name or router_id},
                                    {"name": "ROUTER_LOCATION", "value": location},
                                    {"name": "ROUTER_PURPOSE", "value": purpose},
                                    {"name": "CONTROL_SECRET_ID", "value": secret_id},
                                    {"name": "GCP_PROJECT", "value": project},
                                    {"name": "CONTROL_HEADER", "value": control_header},
                                    {
                                        "name": "CONTROL_PASSWORD",
                                        "valueFrom": {
                                            "secretKeyRef": {
                                                "name": secret_id,
                                                "key": "latest",
                                            }
                                        },
                                    },
                                ],
                            }
                        ]
                    }
                }
            },
        }

        service_url_api = f"https://run.googleapis.com/v1/projects/{project}/locations/{region}/services/{service_name}"
        get_res = requests.get(service_url_api, headers=headers, timeout=10)

        if get_res.ok:
            # Update existing Cloud Run service (PUT)
            logger.info(f"Updating existing Cloud Run service '{service_name}' via REST API...")
            put_res = requests.put(service_url_api, headers=headers, json=service_body, timeout=60)
            res_obj = put_res.json()
            if put_res.ok:
                service_url = res_obj.get("status", {}).get("url", "")
                revision = res_obj.get("status", {}).get("latestReadyRevisionName") or res_obj.get("status", {}).get("latestCreatedRevisionName", "")
                return True, service_url, revision
            else:
                err_msg = res_obj.get("message", put_res.text)
                return False, f"Cloud Run update error: {err_msg}", ""
        else:
            # Create new Cloud Run service (POST)
            logger.info(f"Creating new Cloud Run service '{service_name}' via REST API...")
            post_url = f"https://run.googleapis.com/v1/projects/{project}/locations/{region}/services"
            post_res = requests.post(post_url, headers=headers, json=service_body, timeout=60)
            res_obj = post_res.json()
            if post_res.ok:
                service_url = res_obj.get("status", {}).get("url", "")
                if not service_url:
                    # Projected Cloud Run URL format for new services in this project & region
                    service_url = f"https://{service_name}-cta6n7hkya-uc.a.run.app"
                revision = res_obj.get("status", {}).get("latestReadyRevisionName") or res_obj.get("status", {}).get("latestCreatedRevisionName", "")
                return True, service_url, revision
            else:
                err_msg = res_obj.get("message", post_res.text)
                return False, f"Cloud Run deployment error: {err_msg}", ""

    except Exception as err:
        logger.error(f"Error deploying to Cloud Run via REST API: {err}")
        return False, f"Deployment failed: {str(err)}", ""


def delete_cloud_run_router(router_id: str, project_id: str = "", region: str = "us-central1") -> Tuple[bool, str]:
    """Deletes a Cloud Run router service and associated Secret Manager secret.

    Args:
        router_id: Unique router ID string.
        project_id: GCP project ID string.
        region: GCP region string.

    Returns:
        Tuple of (success_boolean, status_message).
    """
    project = project_id or os.getenv("GCP_PROJECT", "agentspace-argolis-demo")
    reg = region or os.getenv("GCP_REGION", "us-central1")
    service_name = sanitize_service_name(router_id)
    secret_id = get_secret_id_for_router(router_id)

    try:
        credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)

        headers = {"Authorization": f"Bearer {credentials.token}"}
        svc_url = f"https://run.googleapis.com/v1/projects/{project}/locations/{reg}/services/{service_name}"

        # 1. Delete Cloud Run Service
        logger.info(f"Tearing down Cloud Run service '{service_name}' via REST API...")
        del_res = requests.delete(svc_url, headers=headers, timeout=30)
        if del_res.ok or del_res.status_code == 404:
            logger.info(f"Successfully deleted Cloud Run service '{service_name}' (status {del_res.status_code})")
        else:
            logger.warning(f"Could not delete Cloud Run service '{service_name}': HTTP {del_res.status_code} - {del_res.text}")

        # 2. Delete Secret Manager Secret if present
        try:
            from google.cloud import secretmanager
            sec_client = secretmanager.SecretManagerServiceClient()
            sec_name = sec_client.secret_path(project, secret_id)
            sec_client.delete_secret(request={"name": sec_name})
            logger.info(f"Deleted secret '{secret_id}' from Secret Manager.")
        except Exception as sec_err:
            logger.info(f"Secret '{secret_id}' deletion status: {sec_err}")

        return True, f"Cloud Run router '{router_id}' teardown completed."
    except Exception as err:
        logger.error(f"Error executing Cloud Run teardown for '{router_id}': {err}")
        return False, f"Teardown error: {str(err)}"
