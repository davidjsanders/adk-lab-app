#!/usr/bin/env bash
# Production Deployment Script for Router Fleet Operations MCP Server to Cloud Run
# Provisions dedicated Service Account with identical IAM permissions as router-dashboard-sa
# Enforces IAM security (--no-allow-unauthenticated)

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration variables with sensible defaults
SERVICE_NAME="${SERVICE_NAME:-router-mcp-server}"
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project 2>/dev/null || echo "adk-lab-app-dev")}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
SA_NAME="${SA_NAME:-router-mcp-server-sa}"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
REGISTRY_BASE="${REGISTRY_BASE:-us-central1-docker.pkg.dev/agentspace-argolis-demo/docker-registry}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
IMAGE_URI="${REGISTRY_BASE}/${SERVICE_NAME}:${IMAGE_TAG}"

echo "========================================================================="
echo " Deploying Router MCP Server to GCP Cloud Run"
echo " Service Name    : ${SERVICE_NAME}"
echo " Service Account : ${SA_EMAIL}"
echo " GCP Project     : ${PROJECT_ID}"
echo " GCP Region      : ${REGION}"
echo " Image Target    : ${IMAGE_URI}"
echo " Security Model  : IAM Protected (--no-allow-unauthenticated)"
echo "========================================================================="

# Verification checks
if ! command -v docker &>/dev/null; then
    echo "Error: docker CLI is required but not installed." >&2
    exit 1
fi

if ! command -v gcloud &>/dev/null; then
    echo "Error: gcloud CLI is required but not installed." >&2
    exit 1
fi

# Step 1: Provision Service Account & Grant Required Roles
echo "--> Step 1: Provisioning dedicated Service Account '${SA_NAME}'..."
if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" &>/dev/null; then
    echo "  -> Creating Service Account '${SA_NAME}'..."
    gcloud iam service-accounts create "${SA_NAME}" \
        --project="${PROJECT_ID}" \
        --display-name="Router MCP Server Service Account"
    echo "  -> Waiting 10s for Service Account IAM propagation..."
    sleep 10
else
    echo "  -> Service Account '${SA_NAME}' already exists."
fi

# Assign identical IAM permissions as router-dashboard-sa
ROLES=(
    "roles/logging.logWriter"
    "roles/cloudtrace.agent"
    "roles/run.invoker"
    "roles/run.admin"
    "roles/iam.serviceAccountUser"
    "roles/secretmanager.secretAccessor"
    "roles/secretmanager.admin"
    "roles/iam.serviceAccountTokenCreator"
    "roles/artifactregistry.reader"
)

echo "--> Step 2: Binding IAM roles to Service Account '${SA_EMAIL}'..."
for role in "${ROLES[@]}"; do
    echo "  -> Binding role '${role}'..."
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="${role}" \
        --quiet >/dev/null
done

# Step 3: Configure Docker authentication for Artifact Registry
echo "--> Step 3: Authenticating Docker with Artifact Registry..."
REGISTRY_HOST="$(echo "$REGISTRY_BASE" | cut -d'/' -f1)"
gcloud auth configure-docker "$REGISTRY_HOST" --quiet || {
    echo "Warning: gcloud docker auth config returned non-zero. Continuing if pre-authenticated."
}

# Step 4: Build Multi-Stage Docker Image
echo "--> Step 4: Building Docker container image with uv..."
docker build \
    --platform linux/amd64 \
    -t "${IMAGE_URI}" \
    -f Dockerfile .

# Step 5: Push Docker Image to Registry
echo "--> Step 5: Pushing image to registry '${IMAGE_URI}'..."
docker push "${IMAGE_URI}"

# Step 6: Deploy Container Image to Cloud Run bound to Dedicated SA with IAM Protection
echo "--> Step 6: Deploying container image to Cloud Run bound to '${SA_EMAIL}'..."
gcloud run deploy "${SERVICE_NAME}" \
    --image="${IMAGE_URI}" \
    --service-account="${SA_EMAIL}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --platform=managed \
    --concurrency=80 \
    --timeout=300 \
    --no-allow-unauthenticated \
    --set-env-vars="DASHBOARD_URL=${DASHBOARD_URL:-https://router-dashboard-cta6n7hkya-uc.a.run.app}"

echo "========================================================================="
echo " Successfully deployed ${SERVICE_NAME} to Cloud Run!"
echo " Service Account : ${SA_EMAIL}"
echo " Service Endpoint URL:"
gcloud run services describe "${SERVICE_NAME}" --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)"
echo "========================================================================="
