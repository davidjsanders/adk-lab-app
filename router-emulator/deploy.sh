#!/usr/bin/env bash
# Copyright 2026 Google LLC
# Production deployment script for Router Emulator to Cloud Run from container image.
# Strictly enforces IAM protection (--no-allow-unauthenticated).

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -f "cloudrun.env" ]]; then
    set -o allexport
    source cloudrun.env
    set +o allexport
elif [[ -f ".env" ]]; then
    set -o allexport
    source .env
    set +o allexport
fi

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo "adk-lab-app-dev")}"
SERVICE_NAME="${SERVICE_NAME:-router-emulator-01}"
REGION="${REGION:-us-central1}"
REGISTRY_BASE="${REGISTRY_BASE:-us-central1-docker.pkg.dev/agentspace-argolis-demo/docker-registry}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
IMAGE_URI="${REGISTRY_BASE}/${SERVICE_NAME}:${IMAGE_TAG}"

ROUTER_ID="${ROUTER_ID:-RTR-CLOUD-01}"
ROUTER_LOCATION="${ROUTER_LOCATION:-Google Cloud Run Region ${REGION}}"
ROUTER_PURPOSE="${ROUTER_PURPOSE:-Virtual Core Edge Router}"
MANUFACTURER_ID="${MANUFACTURER_ID:-CISCO-CLOUD-VIRTUAL-8000}"
FIRMWARE_VERSION="${FIRMWARE_VERSION:-v5.2.1-CLOUD}"
CONTROL_PASSWORD="${CONTROL_PASSWORD:-CloudRouterSecureKey2026!}"
CONTROL_HEADER="${CONTROL_HEADER:-X-Control-Password}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

echo "=========================================================="
echo " Deploying Router Emulator Service to Cloud Run"
echo " Service Name:     $SERVICE_NAME"
echo " Project ID:       $PROJECT_ID"
echo " Region:           $REGION"
echo " Registry Image:   $IMAGE_URI"
echo " Access Security:  IAM Protected (--no-allow-unauthenticated)"
echo "=========================================================="

REGISTRY_HOST="$(echo "$REGISTRY_BASE" | cut -d'/' -f1)"
gcloud auth configure-docker "$REGISTRY_HOST" --quiet || true

echo "--> Step 1: Building multi-stage container image with uv..."
docker build --platform linux/amd64 -t "$IMAGE_URI" -f Dockerfile .

echo "--> Step 2: Pushing image to registry '$IMAGE_URI'..."
docker push "$IMAGE_URI"

echo "--> Step 3: Deploying container image to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_URI" \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --concurrency 80 \
    --timeout 300 \
    --no-allow-unauthenticated \
    --set-env-vars "ROUTER_ID=$ROUTER_ID,ROUTER_LOCATION=$ROUTER_LOCATION,ROUTER_PURPOSE=$ROUTER_PURPOSE,MANUFACTURER_ID=$MANUFACTURER_ID,FIRMWARE_VERSION=$FIRMWARE_VERSION,CONTROL_PASSWORD=$CONTROL_PASSWORD,CONTROL_HEADER=$CONTROL_HEADER,LOG_LEVEL=$LOG_LEVEL"

echo "=========================================================="
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)' 2>/dev/null || echo "Unknown")
echo " Router Emulator Deployment Completed!"
echo " Service URL: $SERVICE_URL"
echo "=========================================================="
