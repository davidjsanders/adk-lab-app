#!/usr/bin/env bash
set -euo pipefail

# Configuration
PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null || echo "agentspace-argolis-demo")}"
ACTION="${2:-deploy}" # "deploy" or "publish"
REGION="us-central1"
SA_NAME="sysman-ops-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
REGISTRY="us-central1-docker.pkg.dev/${PROJECT_ID}/docker-registry"
PROJECT_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
ACTIVE_USER=$(gcloud config get-value account 2>/dev/null || echo "")

FAST_MODEL="gemini-3-flash-preview"
PRO_MODEL="gemini-3.1-pro-preview"

echo "========================================================================="
echo "SysMan Ops Agent Action: ${ACTION} | Project: ${PROJECT_ID}"
echo "========================================================================="

if [ "${ACTION}" = "deploy" ]; then
  # 1. Construct downstream and local agent URLs deterministically
  echo "Constructing agent URLs..."
  URL_DETECTION="https://sysman-detection-agent-${PROJECT_NUMBER}.${REGION}.run.app"
  URL_DIAGNOSIS="https://sysman-diagnosis-agent-${PROJECT_NUMBER}.${REGION}.run.app"
  URL_OPS="https://sysman-ops-agent-${PROJECT_NUMBER}.${REGION}.run.app"

  # 2. Deploy to Cloud Run using agents-cli
  echo "Deploying sysman-ops-agent using agents-cli with APP_URL=${URL_OPS}..."
  agents-cli deploy \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --service-account="${SA_EMAIL}" \
    --memory="2Gi" \
    --cpu="2" \
    --min-instances=1 \
    --no-confirm-project \
    --update-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=True,DETECTION_AGENT_URL=${URL_DETECTION},DIAGNOSIS_AGENT_URL=${URL_DIAGNOSIS},FAST_MODEL=${FAST_MODEL},PRO_MODEL=${PRO_MODEL},APP_URL=${URL_OPS}"


fi

# Resolve URL_OPS
URL_OPS="https://sysman-ops-agent-${PROJECT_NUMBER}.${REGION}.run.app"


if [ "${ACTION}" = "deploy" ]; then
  # 5. Grant invoker permissions on downstream agents to orchestrator
  echo "Granting invoker permissions to downstream agents..."
  for svc in sysman-detection-agent sysman-diagnosis-agent; do
    gcloud run services add-iam-policy-binding "${svc}" \
      --project="${PROJECT_ID}" \
      --region="${REGION}" \
      --member="serviceAccount:${SA_EMAIL}" \
      --role="roles/run.invoker" \
      --quiet || true
  done

  # Grant active user and platform invoker permissions
  DISCOVERY_ENGINE_SA="service-${PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
  gcloud run services add-iam-policy-binding sysman-ops-agent \
    --project="${PROJECT_ID}" \
    --region="${REGION}" \
    --member="serviceAccount:${DISCOVERY_ENGINE_SA}" \
    --role="roles/run.invoker" \
    --quiet || true

  if [ -n "${ACTIVE_USER}" ]; then
    gcloud run services add-iam-policy-binding sysman-ops-agent \
      --project="${PROJECT_ID}" \
      --region="${REGION}" \
      --member="user:${ACTIVE_USER}" \
      --role="roles/run.invoker" \
      --quiet || true
  fi

  # 6. Save deployment metadata
  echo "Writing deployment_metadata.json..."
  cat <<EOF > deployment_metadata.json
{
  "remote_agent_runtime_id": "${URL_OPS}",
  "deployment_target": "cloud_run",
  "deployment_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
fi

# 7. Register with Gemini Enterprise
GEMINI_APP="${GEMINI_ENTERPRISE_APP_ID:-projects/${PROJECT_NUMBER}/locations/us/collections/default_collection/engines/agentspace-exemplar_1755693787640}"
if [ -n "${GEMINI_APP}" ]; then
  if [ "${ACTION}" = "deploy" ]; then
    echo "Waiting 60 seconds for Cloud Run routing and discovery stabilization before registering..."
    sleep 60
  fi
  echo "Registering with Gemini Enterprise..."
  agents-cli publish gemini-enterprise \
    --registration-type a2a \
    --agent-card-url "${URL_OPS}/a2a/app/.well-known/agent-card.json" \
    --gemini-enterprise-app-id "${GEMINI_APP}" \
    --deployment-target cloud_run || echo "Warning: Gemini Enterprise registration skipped."
fi

echo "========================================================================="
echo "Action ${ACTION} Complete!"
echo "Orchestrator URL: ${URL_OPS}"
echo "========================================================================="
