#!/bin/bash
# Script to stand up the Jira Specialist Agent local environment.

set -e

# Base directory setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Global ports
PORT_JIRA_EMULATOR=8082
MCP_PORT=8005

# Clean up any stale port bindings from previous runs first
echo "Cleaning up any stale port bindings (8082, 8005)..."
fuser -k 8082/tcp 8005/tcp >/dev/null 2>&1 || true
sleep 2

# Active models & credentials
export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-agentspace-argolis-demo}"
export GOOGLE_CLOUD_LOCATION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
export GOOGLE_GENAI_USE_VERTEXAI="True"
export FAST_MODEL="${FAST_MODEL:-gemini-3-flash-preview}"
export PRO_MODEL="${PRO_MODEL:-gemini-3.1-pro-preview}"
export IMPERSONATE_SA="sysman-ops-sa@agentspace-argolis-demo.iam.gserviceaccount.com"

# Connections configuration
export MCP_SERVER_URL="http://127.0.0.1:$MCP_PORT"

# Bypassing google-auth's gcloud fallback logic by copying ADC to a custom path
DEFAULT_ADC_PATH="$HOME/.config/gcloud/application_default_credentials.json"
TEMP_ADC_PATH="$WORKSPACE_DIR/logs/adc_temp.json"

if [ -f "$DEFAULT_ADC_PATH" ]; then
  mkdir -p "$WORKSPACE_DIR/logs"
  cp "$DEFAULT_ADC_PATH" "$TEMP_ADC_PATH"
  export GOOGLE_APPLICATION_CREDENTIALS="$TEMP_ADC_PATH"
fi

# Clean up variables
JIRA_EMULATOR_PID=""
MCP_PID=""

# Helper to log to active terminal device directly
log_tty() {
  if [ -c /dev/tty ]; then
    echo -e "$1" > /dev/tty
  else
    echo -e "$1"
  fi
}

cleanup() {
  log_tty "\n=============================================="
  log_tty "Shutting down background services..."
  log_tty "=============================================="
  
  if [ -n "$JIRA_EMULATOR_PID" ]; then
    log_tty "Stopping Jira Emulator (PID: $JIRA_EMULATOR_PID)..."
    kill "$JIRA_EMULATOR_PID" 2>/dev/null || true
  fi
  if [ -n "$MCP_PID" ]; then
    log_tty "Stopping MCP Server (PID: $MCP_PID)..."
    kill "$MCP_PID" 2>/dev/null || true
  fi

  log_tty "Cleaning up local port bindings (8082, 8005)..."
  fuser -k 8082/tcp 8005/tcp >/dev/null 2>&1 || true
  rm -f "$WORKSPACE_DIR/logs/adc_temp.json" 2>/dev/null || true

  sleep 1
  log_tty "=============================================="
  log_tty "All services successfully stopped."
  log_tty "=============================================="
}

# Trap exits/interrupts
trap cleanup EXIT INT TERM

echo "=============================================="
echo " Starting SysMan-v2 Jira Local Env"
echo "=============================================="

# Ensure logs directory exists
mkdir -p "$WORKSPACE_DIR/logs"

# 1. Start Jira Emulator
echo "Starting Jira Emulator on port $PORT_JIRA_EMULATOR..."
cd "$WORKSPACE_DIR/sysman-v2/sysman-emulator"
PORT=$PORT_JIRA_EMULATOR EMULATOR_CONFIG_PATH="config/jira_config.json" CONTROL_PASSWORD="TestPass123!" uv run python app.py > "$WORKSPACE_DIR/logs/sysman-v2-emulator-jira.log" 2>&1 &
JIRA_EMULATOR_PID=$!

# 2. Start MCP Server
echo "Starting MCP Server on port $MCP_PORT..."
cd "$WORKSPACE_DIR/sysman-v2/sysman-mcp-server"
PORT=$MCP_PORT \
SYSTEM_EMULATORS='{"jira-app-01": "http://127.0.0.1:8082"}' \
CONTROL_PASSWORD="TestPass123!" \
CONTROL_HEADER="X-Control-Password" \
uv run python server.py > "$WORKSPACE_DIR/logs/sysman-v2-mcp.log" 2>&1 &
MCP_PID=$!

# Wait for MCP server to initialize
sleep 3

echo "=============================================="
echo " Launching Jira Specialist Playground..."
echo "=============================================="

# Launch playground for the Jira role
cd "$WORKSPACE_DIR/sysman-v2/sysman-agent"
export AGENT_ROLE="specialist"
export AGENT_CONFIG_FILE="jira-prd.json"
uv run agents-cli playground
