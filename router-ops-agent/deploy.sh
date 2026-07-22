#!/usr/bin/env bash
set -euo pipefail

# Configuration
TARGET="${1:-cloud_run}"

if [ "${TARGET}" = "agent_runtime" ]; then
  exec ./deploy_agent_runtime.sh "$@"
fi

PROJECT_ID="agentspace-argolis-demo"
REGION="us-central1"
SERVICE_NAME="router-ops-agent"
SA_NAME="router-ops-agent-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
REGISTRY="us-central1-docker.pkg.dev/${PROJECT_ID}/docker-registry"
IMAGE_URI="${REGISTRY}/${SERVICE_NAME}:latest"
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
ACTIVE_USER=$(gcloud config get-value account 2>/dev/null || echo "")

echo "========================================================================="
echo "Deploying ${SERVICE_NAME} to Cloud Run in project ${PROJECT_ID} (${REGION})"
echo "========================================================================="

# 1. Create Dedicated Service Account if it doesn't exist
echo "Step 1: Checking Service Account ${SA_EMAIL}..."
if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  echo "Creating dedicated Service Account ${SA_NAME}..."
  gcloud iam service-accounts create "${SA_NAME}" \
    --project="${PROJECT_ID}" \
    --display-name="Router Ops Agent Service Account"
else
  echo "Service Account ${SA_EMAIL} already exists."
fi

# 2. Grant Required IAM Roles to the Service Account
echo "Step 2: Assigning IAM roles to Service Account..."
REQUIRED_ROLES=(
  "roles/aiplatform.user"
  "roles/logging.logWriter"
  "roles/secretmanager.secretAccessor"
  "roles/storage.objectAdmin"
  "roles/run.invoker"
  "roles/cloudtrace.agent"
  "roles/telemetry.tracesWriter"
)

for role in "${REQUIRED_ROLES[@]}"; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${role}" \
    --condition=None >/dev/null 2>&1 || true
done
echo "IAM roles successfully assigned to ${SA_EMAIL}."

# 3. Configure Docker Authentication & Build Image
echo "Step 3: Building and pushing Docker container image..."
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
docker build -t "${IMAGE_URI}" .
docker push "${IMAGE_URI}"

# 4. Deploy to Cloud Run (strictly authenticated, non-root runner, dedicated SA)
echo "Step 4: Deploying image to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --image="${IMAGE_URI}" \
  --service-account="${SA_EMAIL}" \
  --no-allow-unauthenticated \
  --memory="2Gi" \
  --cpu="2" \
  --min-instances=0 \
  --no-cpu-throttling \
  --env-vars-file="env.yaml"

SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)")
echo "Cloud Run service deployed at: ${SERVICE_URL}"

# 5. Grant Invoker permissions for Gemini Enterprise / Agent Registry and active user
echo "Step 5: Granting Cloud Run Invoker permissions..."
DISCOVERY_ENGINE_SA="service-${PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
gcloud run services add-iam-policy-binding "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --member="serviceAccount:${DISCOVERY_ENGINE_SA}" \
  --role="roles/run.invoker" \
  --quiet || true

if [ -n "${ACTIVE_USER}" ]; then
  gcloud run services add-iam-policy-binding "${SERVICE_NAME}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --member="user:${ACTIVE_USER}" \
    --role="roles/run.invoker" \
    --quiet || true
fi

# 6. Save deployment metadata
echo "Step 6: Writing deployment_metadata.json..."
cat <<EOF > deployment_metadata.json
{
  "remote_agent_runtime_id": "${SERVICE_URL}",
  "remote_agent_engine_id": "${SERVICE_URL}",
  "deployment_target": "cloud_run",
  "deployment_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

echo "========================================================================="
echo "Deployment Complete!"
echo "Service URL: ${SERVICE_URL}"
echo "Agent Card URL: ${SERVICE_URL}/a2a/app/.well-known/agent-card.json"
echo "========================================================================="
