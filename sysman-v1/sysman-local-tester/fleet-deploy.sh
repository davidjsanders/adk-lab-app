#!/usr/bin/env bash
# Fleet Deployment Orchestrator for SysMan Suite
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null || echo "agentspace-argolis-demo")}"
START_STEP="${2:-emulators}"

echo "========================================================================="
echo " Starting Orchestrated Fleet Deployment for SysMan Suite"
echo " Target Project: ${PROJECT_ID} | Start Step: ${START_STEP}"
echo "========================================================================="

should_run() {
  local step="$1"
  local start="$2"
  local val_step=0
  local val_start=0

  case "$step" in
    emulators)   val_step=1 ;;
    mcp)         val_step=2 ;;
    detection)   val_step=3 ;;
    diagnosis)   val_step=4 ;;
    ops|publish) val_step=5 ;;
  esac

  case "$start" in
    emulators)   val_start=1 ;;
    mcp)         val_start=2 ;;
    detection)   val_start=3 ;;
    diagnosis)   val_start=4 ;;
    ops|publish) val_start=5 ;;
  esac

  if [ "$val_step" -ge "$val_start" ]; then
    return 0
  else
    return 1
  fi
}

# 1. Deploy Emulators
if should_run "emulators" "${START_STEP}"; then
  echo -e "\n>>> Deploying Emulators..."
  cd "${WORKSPACE_DIR}/sysman-v1/sysman-emulator"
  ./deploy.sh "${PROJECT_ID}"
fi

# 2. Deploy MCP Server
if should_run "mcp" "${START_STEP}"; then
  echo -e "\n>>> Deploying MCP Server..."
  cd "${WORKSPACE_DIR}/sysman-v1/sysman-mcp-server"
  ./deploy.sh "${PROJECT_ID}"
fi

# 3. Deploy Downstream Agent: Detection
if should_run "detection" "${START_STEP}"; then
  echo -e "\n>>> Deploying Detection Agent..."
  cd "${WORKSPACE_DIR}/sysman-v1/sysman-detection-agent"
  ./deploy.sh "${PROJECT_ID}"
fi

# 4. Deploy Downstream Agent: Diagnosis
if should_run "diagnosis" "${START_STEP}"; then
  echo -e "\n>>> Deploying Diagnosis Agent..."
  cd "${WORKSPACE_DIR}/sysman-v1/sysman-diagnosis-agent"
  ./deploy.sh "${PROJECT_ID}"
fi

# 5. Deploy Orchestrator Agent: Ops
if should_run "ops" "${START_STEP}"; then
  echo -e "\n>>> Deploying Orchestrator Agent..."
  cd "${WORKSPACE_DIR}/sysman-v1/sysman-ops-agent"
  
  action="deploy"
  if [ "${START_STEP}" = "publish" ]; then
    action="publish"
  fi
  ./deploy.sh "${PROJECT_ID}" "${action}"
fi

echo "========================================================================="
echo " Fleet Deployment Successfully Completed!"
echo "========================================================================="
