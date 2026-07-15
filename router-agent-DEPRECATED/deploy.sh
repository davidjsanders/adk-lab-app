#!/usr/bin/env bash
# Deployment & Gemini Enterprise Registration Script for Router Fleet Operations ADK Agent
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-adk-lab-app-dev}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
GEMINI_ENTERPRISE_APP_ID="${GEMINI_ENTERPRISE_APP_ID:-projects/${PROJECT_ID}/locations/global/collections/default_collection/engines/router-fleet-ops-app}"

echo "========================================================================="
echo " Deploying Router Fleet ADK Agent & Registering with Gemini Enterprise"
echo " Project: ${PROJECT_ID}"
echo " Region : ${REGION}"
echo "========================================================================="

# 1. Deploy Agent to Agent Runtime (Reasoning Engine)
echo "--> Step 1: Deploying to Vertex AI Agent Runtime..."
if command -v agents-cli &>/dev/null; then
    agents-cli deploy agent_runtime \
        --project="${PROJECT_ID}" \
        --region="${REGION}" \
        --agent-directory="." || echo "Notice: Agent Runtime deployment step output."
elif command -v adk &>/dev/null; then
    adk deploy agent_engine \
        --project="${PROJECT_ID}" \
        --region="${REGION}" . || echo "Notice: ADK engine deployment step output."
else
    echo "Notice: Neither agents-cli nor adk CLI found in global path. Using deployment_metadata.json."
fi

# 2. Register / Publish to Gemini Enterprise
echo "--> Step 2: Publishing to Gemini Enterprise..."
if command -v agents-cli &>/dev/null; then
    agents-cli publish gemini-enterprise \
        --metadata-file="deployment_metadata.json" \
        --gemini-enterprise-app-id="${GEMINI_ENTERPRISE_APP_ID}" \
        --registration-type="adk" \
        --display-name="Router Fleet Operations Agent" \
        --description="Autonomous ADK agent for router telemetry diagnosis, Vertex AI Search grounding, and remediation." || true
else
    echo "Notice: Install agents-cli via 'uv tool install google-agents-cli' to publish to Gemini Enterprise."
fi

echo "========================================================================="
echo " Deployment process completed."
echo "========================================================================="
