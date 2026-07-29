#!/usr/bin/env bash
set -euo pipefail

# Configuration
PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null || echo "agentspace-argolis-demo")}"
REGION="us-central1"
SA_NAME="sysman-ops-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
REGISTRY="us-central1-docker.pkg.dev/${PROJECT_ID}/docker-registry"

FAST_MODEL="gemini-3-flash-preview"
PRO_MODEL="gemini-3.1-pro-preview"

echo "========================================================================="
echo "Deploying Detection Agent (sysman-detection-agent) to Cloud Run"
echo "Project: ${PROJECT_ID} | Region: ${REGION}"
echo "========================================================================="

# 1. Resolve MCP Server URL
echo "Resolving MCP Server URL..."
URL_MCP=$(gcloud run services describe sysman-mcp-server --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)" 2>/dev/null || echo "")

if [ -z "${URL_MCP}" ]; then
  echo "Error: MCP Server (sysman-mcp-server) is not deployed yet."
  echo "Please deploy it first before deploying the detection agent."
  exit 1
fi

# 2. Resolve project number and construct deterministic URL
echo "Resolving project number..."
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
URL_DETECTION="https://sysman-detection-agent-${PROJECT_NUMBER}.${REGION}.run.app"

# Deploy to Cloud Run using agents-cli
echo "Deploying sysman-detection-agent using agents-cli with APP_URL=${URL_DETECTION}..."
agents-cli deploy \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --service-account="${SA_EMAIL}" \
  --memory="2Gi" \
  --cpu="2" \
  --min-instances=1 \
  --no-confirm-project \
  --update-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=True,MCP_SERVER_URL=${URL_MCP},FAST_MODEL=${FAST_MODEL},PRO_MODEL=${PRO_MODEL},APP_URL=${URL_DETECTION}"





# 5. Grant invoker permissions on MCP server to detection agent identity
echo "Granting detection agent invoker permissions on MCP server..."
gcloud run services add-iam-policy-binding sysman-mcp-server \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.invoker" \
  --quiet || true

echo "========================================================================="
echo "Detection Agent Deployed Successfully!"
echo "Detection Agent URL: ${URL_DETECTION}"
echo "========================================================================="
