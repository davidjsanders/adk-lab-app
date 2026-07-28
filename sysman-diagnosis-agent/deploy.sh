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
echo "Deploying Diagnosis Agent (sysman-diagnosis-agent) to Cloud Run"
echo "Project: ${PROJECT_ID} | Region: ${REGION}"
echo "========================================================================="

# 1. Resolve MCP Server URL
echo "Resolving MCP Server URL..."
URL_MCP=$(gcloud run services describe sysman-mcp-server --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)" 2>/dev/null || echo "")

if [ -z "${URL_MCP}" ]; then
  echo "Error: MCP Server (sysman-mcp-server) is not deployed yet."
  echo "Please deploy it first before deploying the diagnosis agent."
  exit 1
fi

# 2. Deploy to Cloud Run using agents-cli
echo "Deploying sysman-diagnosis-agent using agents-cli..."
agents-cli deploy \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --service-account="${SA_EMAIL}" \
  --memory="2Gi" \
  --cpu="1" \
  --min-instances=1 \
  --no-confirm-project \
  --update-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=True,MCP_SERVER_URL=${URL_MCP},FAST_MODEL=${FAST_MODEL},PRO_MODEL=${PRO_MODEL}"

URL_DIAGNOSIS=$(gcloud run services describe sysman-diagnosis-agent --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)")

# 5. Grant invoker permissions on MCP server to diagnosis agent identity
echo "Granting diagnosis agent invoker permissions on MCP server..."
gcloud run services add-iam-policy-binding sysman-mcp-server \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.invoker" \
  --quiet || true

echo "========================================================================="
echo "Diagnosis Agent Deployed Successfully!"
echo "Diagnosis Agent URL: ${URL_DIAGNOSIS}"
echo "========================================================================="
