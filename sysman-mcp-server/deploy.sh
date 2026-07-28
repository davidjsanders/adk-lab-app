#!/usr/bin/env bash
# Production deployment script for SysMan MCP Server to Cloud Run from container image.
# Enforces IAM protection (--no-allow-unauthenticated).

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -f ".env" ]]; then
    set -o allexport
    source .env
    set +o allexport
fi

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo "agentspace-argolis-demo")}"
SERVICE_NAME="${SERVICE_NAME:-sysman-mcp-server}"
REGION="${REGION:-us-central1}"
REGISTRY_BASE="${REGISTRY_BASE:-us-central1-docker.pkg.dev/agentspace-argolis-demo/docker-registry}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
IMAGE_URI="${REGISTRY_BASE}/${SERVICE_NAME}:${IMAGE_TAG}"

EMULATOR_URL="${EMULATOR_URL:-https://sysman-emulator-63466983700.us-central1.run.app}"
CONTROL_PASSWORD="${CONTROL_PASSWORD:-SysManSecretPass123!}"
CONTROL_HEADER="${CONTROL_HEADER:-X-Control-Password}"

echo "=========================================================="
echo " Deploying SysMan MCP Server to Cloud Run"
echo " Service Name:     $SERVICE_NAME"
echo " Project ID:       $PROJECT_ID"
echo " Region:           $REGION"
echo " Registry Image:   $IMAGE_URI"
echo " Access Security:  IAM Protected (--no-allow-unauthenticated)"
echo "=========================================================="

REGISTRY_HOST="$(echo "$REGISTRY_BASE" | cut -d'/' -f1)"
gcloud auth configure-docker "$REGISTRY_HOST" --quiet || true

echo "--> Step 1: Building container image..."
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
    --set-env-vars "EMULATOR_URL=$EMULATOR_URL,CONTROL_PASSWORD=$CONTROL_PASSWORD,CONTROL_HEADER=$CONTROL_HEADER"

echo "=========================================================="
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)' 2>/dev/null || echo "Unknown")
echo " SysMan MCP Server Deployment Completed!"
echo " Service URL: $SERVICE_URL"
echo "=========================================================="
