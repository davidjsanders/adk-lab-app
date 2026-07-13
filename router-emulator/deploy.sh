#!/bin/bash
#
# Copyright 2026 Google LLC
#
# Deployment script for Router Emulator to Google Cloud Run
# Enforces IAM protection (--no-allow-unauthenticated) and multi-router configuration.

set -e

# --- Configuration ---
if [[ -f "cloudrun.env" ]]; then
    echo "Loading environment variables from cloudrun.env"
    set -o allexport
    source cloudrun.env
    set +o allexport
elif [[ -f ".env" ]]; then
    echo "Loading environment variables from .env"
    set -o allexport
    source .env
    set +o allexport
fi

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || true)}"
SERVICE_NAME="${SERVICE_NAME:-router-emulator-01}"
REGION="${REGION:-us-central1}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Metadata & Secrets
ROUTER_ID="${ROUTER_ID:-RTR-CLOUD-01}"
ROUTER_LOCATION="${ROUTER_LOCATION:-Google Cloud Run Region ${REGION}}"
ROUTER_PURPOSE="${ROUTER_PURPOSE:-Virtual Core Edge Router}"
MANUFACTURER_ID="${MANUFACTURER_ID:-CISCO-CLOUD-VIRTUAL-8000}"
FIRMWARE_VERSION="${FIRMWARE_VERSION:-v5.2.1-CLOUD}"
CONTROL_PASSWORD="${CONTROL_PASSWORD:-CloudRouterSecureKey2026!}"
CONTROL_HEADER="${CONTROL_HEADER:-X-Control-Password}"

if [[ -z "$PROJECT_ID" ]]; then
    echo "ERROR: PROJECT_ID is missing. Please set PROJECT_ID in cloudrun.env or gcloud configuration."
    exit 1
fi

echo "=========================================================="
echo " Deploying Router Emulator Service to Cloud Run"
echo " Service Name:     $SERVICE_NAME"
echo " Project ID:       $PROJECT_ID"
echo " Region:           $REGION"
echo " Router ID:        $ROUTER_ID"
echo " Control Header:   $CONTROL_HEADER"
echo " Access Security:  IAM Protected (--no-allow-unauthenticated)"
echo "=========================================================="

# Pre-flight Artifact Registry verification
if ! gcloud artifacts repositories describe "cloud-run-source-deploy" --project "$PROJECT_ID" --location "$REGION" &>/dev/null; then
    echo "Creating Artifact Registry repository 'cloud-run-source-deploy'..."
    gcloud artifacts repositories create "cloud-run-source-deploy" \
        --repository-format=docker \
        --location="$REGION" \
        --project="$PROJECT_ID" \
        --description="Cloud Run Source Deploy Repository"
fi

# Deploy to Cloud Run using source build
echo "Executing Cloud Run Deployment..."
gcloud beta run deploy "$SERVICE_NAME" \
    --source . \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --ingress all \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars "ROUTER_ID=$ROUTER_ID,ROUTER_LOCATION=$ROUTER_LOCATION,ROUTER_PURPOSE=$ROUTER_PURPOSE,MANUFACTURER_ID=$MANUFACTURER_ID,FIRMWARE_VERSION=$FIRMWARE_VERSION,CONTROL_PASSWORD=$CONTROL_PASSWORD,CONTROL_HEADER=$CONTROL_HEADER,LOG_LEVEL=$LOG_LEVEL" \
    --no-allow-unauthenticated \
    --quiet

echo "=========================================================="
echo " Router Emulator Deployment Completed!"
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)' 2>/dev/null || echo "Unknown")
echo " Service URL: $SERVICE_URL"
echo " To send commands to this router:"
echo " curl -X POST $SERVICE_URL/api/command \\"
echo "   -H '$CONTROL_HEADER: $CONTROL_PASSWORD' \\"
echo "   -H 'Content-Type: application/json' \\"
echo "   -d '{\"command\": \"bgp_reset\"}'"
echo "=========================================================="
