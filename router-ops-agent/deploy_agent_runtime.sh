#!/usr/bin/env bash
set -euo pipefail

# Configuration
PROJECT_ID="agentspace-argolis-demo"
REGION="us-central1"
SERVICE_NAME="router-ops-agent"
SA_NAME="router-ops-agent-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "========================================================================="
echo "Deploying ${SERVICE_NAME} to Agent Runtime in project ${PROJECT_ID} (${REGION})"
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

# 3. Deploy to Agent Runtime via agents-cli deploy
echo "Step 3: Deploying to Agent Runtime..."
agents-cli deploy \
  --deployment-target agent_runtime \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --service-name "${SERVICE_NAME}" \
  --service-account "${SA_EMAIL}" \
  --cpu 2 \
  --memory 4Gi \
  --min-instances 1 \
  --max-instances 10 \
  --no-confirm-project

echo "========================================================================="
echo "Agent Runtime Deployment Completed!"
echo "========================================================================="
