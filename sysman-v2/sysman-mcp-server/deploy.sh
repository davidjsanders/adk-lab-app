#!/usr/bin/env bash
set -euo pipefail

# Configuration
PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null || echo "agentspace-argolis-demo")}"
REGION="us-central1"
SA_NAME="sysman-ops-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
REGISTRY="us-central1-docker.pkg.dev/${PROJECT_ID}/docker-registry"

echo "========================================================================="
echo "Deploying SysMan MCP Server to Cloud Run"
echo "Project: ${PROJECT_ID} | Region: ${REGION}"
echo "========================================================================="

# 1. Resolve Emulator URLs
echo "Resolving emulator service URLs..."
URL_LINUX=$(gcloud run services describe sysman-emulator-linux --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)" 2>/dev/null || echo "")
URL_JIRA=$(gcloud run services describe sysman-emulator-jira --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)" 2>/dev/null || echo "")
URL_CONFLUENCE=$(gcloud run services describe sysman-emulator-confluence --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)" 2>/dev/null || echo "")

if [ -z "${URL_LINUX}" ] || [ -z "${URL_JIRA}" ] || [ -z "${URL_CONFLUENCE}" ]; then
  echo "Error: Emulators (sysman-emulator-linux, sysman-emulator-jira, sysman-emulator-confluence) are not deployed yet."
  echo "Please deploy them first before deploying the MCP server."
  exit 1
fi

# 2. Build and push image
echo "Building and pushing MCP container image..."
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
MCP_IMAGE="${REGISTRY}/sysman-mcp-server:latest"
docker build -t "${MCP_IMAGE}" .
docker push "${MCP_IMAGE}"

# 3. Create env.yaml config
echo "Creating env.yaml..."
cat <<EOF > env.yaml
SYSTEM_EMULATORS: '{"linux-server-01":"${URL_LINUX}","jira-app-01":"${URL_JIRA}","confluence-app-01":"${URL_CONFLUENCE}"}'
CONTROL_PASSWORD: "TestPass123!"
CONTROL_HEADER: "X-Control-Password"
EOF

# 4. Deploy to Cloud Run
echo "Deploying sysman-mcp-server to Cloud Run..."
gcloud run deploy sysman-mcp-server \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --image="${MCP_IMAGE}" \
  --service-account="${SA_EMAIL}" \
  --no-allow-unauthenticated \
  --memory="2Gi" \
  --cpu="2" \
  --min-instances=1 \
  --env-vars-file="env.yaml"

URL_MCP=$(gcloud run services describe sysman-mcp-server --project="${PROJECT_ID}" --region="${REGION}" --format="value(status.url)")

# 5. Grant invoker permissions on emulators to MCP server identity
echo "Assigning Invoker roles to service account on emulators..."
for svc in sysman-emulator-linux sysman-emulator-jira sysman-emulator-confluence; do
  gcloud run services add-iam-policy-binding "${svc}" \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/run.invoker" \
    --quiet || true
done

echo "========================================================================="
echo "MCP Server Deployed Successfully!"
echo "MCP Server URL: ${URL_MCP}"
echo "========================================================================="
