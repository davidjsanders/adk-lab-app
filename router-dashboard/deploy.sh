#!/usr/bin/env bash
set -eo pipefail

# ==============================================================================
# Router Dashboard Cloud Run Deployment Script
# Provisions dedicated IAM Service Account with logging, tracing, and invoker rights,
# builds container image, and deploys to Cloud Run with Identity-Aware Proxy (--iap).
# ==============================================================================

# Configuration Defaults
PROJECT_ID="${GCP_PROJECT:-agentspace-argolis-demo}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="router-dashboard"
SA_NAME="router-dashboard-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
REGISTRY="us-central1-docker.pkg.dev/${PROJECT_ID}/docker-registry"
IMAGE_URI="${REGISTRY}/${SERVICE_NAME}:latest"
POLLING_INTERVAL="${POLLING_INTERVAL_MS:-1500}"

echo "=========================================================================="
echo " Starting Deployment for ${SERVICE_NAME}"
echo " Project:          ${PROJECT_ID}"
echo " Region:           ${REGION}"
echo " Image:            ${IMAGE_URI}"
echo " Service Account:  ${SA_EMAIL}"
echo " Polling Interval: ${POLLING_INTERVAL}ms"
echo "=========================================================================="

# 1. Provision Dedicated Service Account & Grant Required Roles
echo "[1/4] Ensuring dedicated Service Account exists and binding IAM roles..."
if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" &>/dev/null; then
    echo "  -> Creating Service Account '${SA_NAME}'..."
    gcloud iam service-accounts create "${SA_NAME}" \
        --project="${PROJECT_ID}" \
        --display-name="Router Dashboard Service Account"
    echo "  -> Waiting 10s for Service Account IAM propagation..."
    sleep 10
else
    echo "  -> Service Account '${SA_NAME}' already exists."
fi

# Mandatory Roles: Logging, Tracing, Cloud Run Invoker, Secret Manager, Token Creator, Cloud Run Admin, SA User
ROLES=(
    "roles/logging.logWriter"
    "roles/cloudtrace.agent"
    "roles/run.invoker"
    "roles/run.admin"
    "roles/iam.serviceAccountUser"
    "roles/secretmanager.secretAccessor"
    "roles/iam.serviceAccountTokenCreator"
)

for role in "${ROLES[@]}"; do
    echo "  -> Binding IAM role '${role}' to ${SA_EMAIL}..."
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="${role}" \
        --quiet >/dev/null
done

# 2. Build and Push Container Image to Artifact Registry
echo "[2/4] Building and pushing Docker container image via Cloud Build..."
gcloud builds submit . \
    --project="${PROJECT_ID}" \
    --tag="${IMAGE_URI}"

# 3. Deploy to Cloud Run with Beta IAP enabled (--iap)
echo "[3/4] Deploying '${SERVICE_NAME}' to Cloud Run with Identity-Aware Proxy (--iap)..."
gcloud beta run deploy "${SERVICE_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --image="${IMAGE_URI}" \
    --service-account="${SA_EMAIL}" \
    --memory=1Gi \
    --cpu=1 \
    --iap \
    --no-allow-unauthenticated \
    --set-env-vars="GCP_PROJECT=${PROJECT_ID},POLLING_INTERVAL_MS=${POLLING_INTERVAL}"

# 4. Fetch Active Service URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)")

echo "=========================================================================="
echo " Deployment Successfully Completed!"
echo " Service Name: ${SERVICE_NAME}"
echo " Service URL:  ${SERVICE_URL}"
echo " IAP Protection: ENABLED"
echo " Service Account: ${SA_EMAIL}"
echo "=========================================================================="
