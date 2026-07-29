#!/usr/bin/env bash
set -euo pipefail

# Configuration
PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null || echo "agentspace-argolis-demo")}"
REGION="us-central1"
SA_NAME="sysman-ops-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
REGISTRY="us-central1-docker.pkg.dev/${PROJECT_ID}/docker-registry"

echo "========================================================================="
echo "Deploying SysMan Emulators (Linux, Jira, Confluence) to Cloud Run"
echo "Project: ${PROJECT_ID} | Region: ${REGION}"
echo "========================================================================="

# 1. Create Dedicated Service Account if it doesn't exist
echo "Step 1: Setting up Service Account ${SA_EMAIL}..."
if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${SA_NAME}" \
    --project="${PROJECT_ID}" \
    --display-name="SysMan Suite Service Account"
else
  echo "Service Account already exists."
fi

# 2. Grant IAM role
echo "Step 2: Assigning logging.logWriter role..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/logging.logWriter" \
  --condition=None >/dev/null 2>&1 || true

# 3. Build and push image
echo "Step 3: Building and pushing emulator container image..."
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
EMULATOR_IMAGE="${REGISTRY}/sysman-emulator:latest"
docker build -t "${EMULATOR_IMAGE}" .
docker push "${EMULATOR_IMAGE}"

# 4. Deploy to Cloud Run
# Deploy Linux Emulator
echo "Deploying sysman-emulator-linux..."
gcloud run deploy sysman-emulator-linux \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --image="${EMULATOR_IMAGE}" \
  --service-account="${SA_EMAIL}" \
  --no-allow-unauthenticated \
  --memory="2Gi" \
  --cpu="1" \
  --min-instances=1 \
  --set-env-vars="EMULATOR_CONFIG_PATH=config/linux_config.json,CONTROL_PASSWORD=TestPass123!"

URL_LINUX=$(gcloud run services describe sysman-emulator-linux --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)")

# Deploy Jira Emulator
echo "Deploying sysman-emulator-jira..."
gcloud run deploy sysman-emulator-jira \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --image="${EMULATOR_IMAGE}" \
  --service-account="${SA_EMAIL}" \
  --no-allow-unauthenticated \
  --memory="2Gi" \
  --cpu="1" \
  --min-instances=1 \
  --set-env-vars="EMULATOR_CONFIG_PATH=config/jira_config.json,CONTROL_PASSWORD=TestPass123!"

URL_JIRA=$(gcloud run services describe sysman-emulator-jira --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)")

# Deploy Confluence Emulator
echo "Deploying sysman-emulator-confluence..."
gcloud run deploy sysman-emulator-confluence \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --image="${EMULATOR_IMAGE}" \
  --service-account="${SA_EMAIL}" \
  --no-allow-unauthenticated \
  --memory="2Gi" \
  --cpu="1" \
  --min-instances=1 \
  --set-env-vars="EMULATOR_CONFIG_PATH=config/confluence_config.json,CONTROL_PASSWORD=TestPass123!"

URL_CONFLUENCE=$(gcloud run services describe sysman-emulator-confluence --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)")

echo "========================================================================="
echo "SysMan Emulators Deployed Successfully!"
echo "Linux Emulator: ${URL_LINUX}"
echo "Jira Emulator: ${URL_JIRA}"
echo "Confluence Emulator: ${URL_CONFLUENCE}"
echo "========================================================================="
