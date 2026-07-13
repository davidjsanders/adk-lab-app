#!/bin/bash
# Script to build and push the base Router Emulator container image to Artifact Registry
# The resulting image is used by router-dashboard to instantly spawn emulated router Cloud Run instances.

set -e

# Load configuration from cloudrun.env or .env
if [[ -f "cloudrun.env" ]]; then
    set -o allexport
    source cloudrun.env
    set +o allexport
elif [[ -f ".env" ]]; then
    set -o allexport
    source .env
    set +o allexport
fi

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || true)}"
REGION="${REGION:-us-central1}"
REPOSITORY="${REPOSITORY:-docker-registry}"
IMAGE_NAME="${IMAGE_NAME:-router-emulator}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

if [[ -z "$PROJECT_ID" ]]; then
    echo "ERROR: PROJECT_ID is missing. Set PROJECT_ID in environment or gcloud config."
    exit 1
fi

FULL_IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "=========================================================="
echo " Building Router Emulator Container Image for Artifact Registry"
echo " Project ID:       $PROJECT_ID"
echo " Region:           $REGION"
echo " Repository:       $REPOSITORY"
echo " Image URI:        $FULL_IMAGE_URI"
echo "=========================================================="

# Ensure Artifact Registry repository exists
echo "Ensuring Artifact Registry repository '$REPOSITORY' exists in $REGION..."
gcloud artifacts repositories create "$REPOSITORY" \
    --repository-format=docker \
    --location="$REGION" \
    --project="$PROJECT_ID" 2>/dev/null || true

# Build and push container image using Cloud Build
echo "Submitting build to Google Cloud Build..."
gcloud builds submit --project "$PROJECT_ID" --tag "$FULL_IMAGE_URI" .

echo "=========================================================="
echo " Image Build Completed Successfully!"
echo " Image URI: $FULL_IMAGE_URI"
echo " Configure this URI in router-dashboard as ROUTER_EMULATOR_IMAGE"
echo "=========================================================="
