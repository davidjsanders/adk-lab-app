#!/usr/bin/env python3
"""Local A2A Test Harness for Router Fleet Operations Agent.

Sends a prompt to the Cloud Run hosted A2A endpoint, authenticating via Google Cloud OIDC,
listens to the SSE stream, extracts the generated PNG card, and saves it locally.
"""

import base64
import json
import os
import sys
import uuid
import requests
import google.auth
import google.auth.transport.requests
from google.auth import impersonated_credentials
from google.oauth2 import id_token


# Configuration
PROJECT_ID = "agentspace-argolis-demo"
SERVICE_URL = "https://router-agent-63466983700.us-central1.run.app"
RPC_URL = f"{SERVICE_URL}/a2a/app"
PROMPT = 'show me the image card for "CAN-NN2-CENTRAL-02"'
OUTPUT_FILENAME = "can_nn2_central_02.png"
IMPERSONATE_SA = "router-dashboard-sa@agentspace-argolis-demo.iam.gserviceaccount.com"


def get_oidc_token(audience: str) -> str:
    """Generates a fresh Google Cloud OIDC ID token for the target audience by impersonating a service account.

    Args:
        audience: Audience URL string (e.g. Cloud Run service URL).

    Returns:
        OIDC ID token string.
    """
    print(f"Generating OIDC token for audience: {audience} by impersonating {IMPERSONATE_SA}...")
    source_credentials, _ = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    source_credentials.refresh(auth_req)
    
    target_credentials = impersonated_credentials.Credentials(
        source_credentials=source_credentials,
        target_principal=IMPERSONATE_SA,
        target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    
    impersonated_id_creds = impersonated_credentials.IDTokenCredentials(
        target_credentials=target_credentials,
        target_audience=audience,
        include_email=True,
    )
    impersonated_id_creds.refresh(auth_req)
    return impersonated_id_creds.token


def run_harness():
    """Main execution of the test harness."""
    try:
        token = get_oidc_token(SERVICE_URL)
    except Exception as e:
        print(f"ERROR: Failed to authenticate with Google Cloud: {e}", file=sys.stderr)
        print("Make sure you are logged in using: gcloud auth application-default login", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    # Construct the JSON-RPC SendStreamingMessageRequest payload
    message_id = f"msg-user-{uuid.uuid4()}"
    request_id = f"req-{uuid.uuid4()}"
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "message/send",
        "params": {
            "message": {
                "messageId": message_id,
                "role": "user",
                "parts": [
                    {
                        "kind": "text",
                        "text": PROMPT
                    }
                ]
            }
        }
    }

    print(f"Sending prompt to A2A endpoint: {RPC_URL}")
    print(f"Prompt: {PROMPT!r}")

    try:
        response = requests.post(
            RPC_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=120
        )
    except Exception as e:
        print(f"ERROR: Connection failed: {e}", file=sys.stderr)
        sys.exit(1)

    if response.status_code != 200:
        print(f"ERROR: HTTP {response.status_code} received from server.", file=sys.stderr)
        print(response.text, file=sys.stderr)
        sys.exit(1)

    print("Connection established. Parsing response...")

    # Helper function to save file
    image_saved = False
    def save_png(b64_data, source_name):
        nonlocal image_saved
        print(f"Found PNG image artifact (from {source_name})! Size: {len(b64_data)} base64 chars.")
        try:
            img_bytes = base64.b64decode(b64_data)
            output_path = os.path.abspath(OUTPUT_FILENAME)
            with open(output_path, "wb") as f:
                f.write(img_bytes)
            print(f"SUCCESS: Image saved to {output_path}")
            image_saved = True
        except Exception as err:
            print(f"ERROR: Failed to save image: {err}", file=sys.stderr)

    try:
        event_data = response.json()
    except Exception as err:
        print(f"ERROR: Failed to parse JSON response: {err}", file=sys.stderr)
        sys.exit(1)

    result = event_data.get("result")
    if not result:
        print("ERROR: Response does not contain 'result'. Full response:")
        print(json.dumps(event_data, indent=2))
        sys.exit(1)

    # 1. Parse result.artifacts list
    artifacts = result.get("artifacts")
    if artifacts:
        for art in artifacts:
            art_name = art.get("name", "")
            for part in art.get("parts", []):
                part_root = part.get("root", part)
                file_info = part_root.get("file")
                if file_info and file_info.get("bytes"):
                    if art_name.lower().endswith(".png") or file_info.get("mimeType") == "image/png" or file_info.get("name", "").lower().endswith(".png"):
                        save_png(file_info["bytes"], f"artifact: {art_name}")
                        
    # 2. Parse result.artifact singular
    artifact = result.get("artifact")
    if artifact:
        art_name = artifact.get("name", "")
        for part in artifact.get("parts", []):
            part_root = part.get("root", part)
            file_info = part_root.get("file")
            if file_info and file_info.get("bytes"):
                if art_name.lower().endswith(".png") or file_info.get("mimeType") == "image/png" or file_info.get("name", "").lower().endswith(".png"):
                    save_png(file_info["bytes"], f"artifact: {art_name}")

    # 3. Parse result.status message parts
    status = result.get("status")
    if status and status.get("message"):
        for part in status["message"].get("parts", []):
            part_root = part.get("root", part)
            file_info = part_root.get("file")
            if file_info and file_info.get("bytes"):
                filename = file_info.get("name", "")
                if filename.lower().endswith(".png") or file_info.get("mimeType") == "image/png":
                    save_png(file_info["bytes"], f"status file: {filename}")

    if not image_saved:
        print("Response parsed, but no PNG image artifact was found.")

    if not image_saved:
        print("Stream finished, but no PNG image artifact was found.")


if __name__ == "__main__":
    run_harness()
