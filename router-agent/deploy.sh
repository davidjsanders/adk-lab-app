#!/usr/bin/env bash
set -euo pipefail

# Configuration
PROJECT_ID="agentspace-argolis-demo"
PROJECT_NUMBER="63466983700"
REGION="us-central1"
SERVICE_NAME="router-agent"
SERVICE_ACCOUNT="router-agent-sa@agentspace-argolis-demo.iam.gserviceaccount.com"
REGISTRY_IMAGE="us-central1-docker.pkg.dev/${PROJECT_ID}/docker-registry/${SERVICE_NAME}:latest"
DISCOVERY_ENGINE_SA="service-${PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com"

echo "=== 1. Configuring Docker authentication for Artifact Registry ==="
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet

echo "=== 2. Building Docker Image ==="
docker build -t "${REGISTRY_IMAGE}" .

echo "=== 3. Pushing Docker Image to Registry ==="
docker push "${REGISTRY_IMAGE}"

echo "=== 4. Deploying Service to Cloud Run via agents-cli deploy ==="
agents-cli deploy \
  --deployment-target cloud_run \
  --image "${REGISTRY_IMAGE}" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --service-name "${SERVICE_NAME}" \
  --service-account "${SERVICE_ACCOUNT}" \
  --no-confirm-project

echo "=== 5. Applying IAM Policy (run.servicesInvoker) for Discovery Engine SA ==="
gcloud run services add-iam-policy-binding "${SERVICE_NAME}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --member="serviceAccount:${DISCOVERY_ENGINE_SA}" \
  --role="roles/run.servicesInvoker"

echo "Deployment to Cloud Run completed successfully."
