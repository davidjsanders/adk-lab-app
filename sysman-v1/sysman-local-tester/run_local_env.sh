#!/bin/bash
# Script to stand up all SysMan local processes and launch agents-cli playground.

set -e

# Base directory setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Global ports
PORT_LINUX_EMULATOR=8081
PORT_JIRA_EMULATOR=8082
PORT_CONFLUENCE_EMULATOR=8083
MCP_PORT=8005
DETECTION_PORT=8006
DIAGNOSIS_PORT=8007

# Active models & credentials
export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-agentspace-argolis-demo}"
export GOOGLE_CLOUD_LOCATION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
export GOOGLE_GENAI_USE_VERTEXAI="True"
export FAST_MODEL="${FAST_MODEL:-gemini-3-flash-preview}"
export PRO_MODEL="${PRO_MODEL:-gemini-3.1-pro-preview}"

# Connections configuration
export MCP_SERVER_URL="http://127.0.0.1:$MCP_PORT"
export DETECTION_AGENT_URL="http://127.0.0.1:$DETECTION_PORT"
export DIAGNOSIS_AGENT_URL="http://127.0.0.1:$DIAGNOSIS_PORT"

# Clean up variables
LINUX_EMULATOR_PID=""
JIRA_EMULATOR_PID=""
CONFLUENCE_EMULATOR_PID=""
MCP_PID=""
DETECTION_PID=""
DIAGNOSIS_PID=""

# Helper to log to active terminal device directly, avoiding REPL swallow
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
  
  if [ -n "$LINUX_EMULATOR_PID" ]; then
    log_tty "Stopping Linux Emulator (PID: $LINUX_EMULATOR_PID)..."
    kill "$LINUX_EMULATOR_PID" 2>/dev/null || true
  fi
  if [ -n "$JIRA_EMULATOR_PID" ]; then
    log_tty "Stopping Jira Emulator (PID: $JIRA_EMULATOR_PID)..."
    kill "$JIRA_EMULATOR_PID" 2>/dev/null || true
  fi
  if [ -n "$CONFLUENCE_EMULATOR_PID" ]; then
    log_tty "Stopping Confluence Emulator (PID: $CONFLUENCE_EMULATOR_PID)..."
    kill "$CONFLUENCE_EMULATOR_PID" 2>/dev/null || true
  fi
  if [ -n "$MCP_PID" ]; then
    log_tty "Stopping MCP Server (PID: $MCP_PID)..."
    kill "$MCP_PID" 2>/dev/null || true
  fi
  if [ -n "$DETECTION_PID" ]; then
    log_tty "Stopping Detection Agent (PID: $DETECTION_PID)..."
    kill "$DETECTION_PID" 2>/dev/null || true
  fi
  if [ -n "$DIAGNOSIS_PID" ]; then
    log_tty "Stopping Diagnosis Agent (PID: $DIAGNOSIS_PID)..."
    kill "$DIAGNOSIS_PID" 2>/dev/null || true
  fi

  log_tty "Cleaning up local port bindings (8081, 8082, 8083, 8005, 8006, 8007)..."
  # Force kill anything remaining on local environment ports
  fuser -k 8081/tcp 8082/tcp 8083/tcp 8005/tcp 8006/tcp 8007/tcp 2>/dev/null || true

  # Wait to allow clean shutdown
  sleep 1
  log_tty "=============================================="
  log_tty "All services successfully stopped."
  log_tty "=============================================="
}

# Trap exits/interrupts
trap cleanup EXIT INT TERM

echo "=============================================="
echo " Starting SysMan Operations Local Environment"
echo "=============================================="

# Ensure logs directory exists
mkdir -p "$WORKSPACE_DIR/logs"

# 1. Start Emulators
echo "Starting Linux Emulator on port $PORT_LINUX_EMULATOR..."
cd "$WORKSPACE_DIR/sysman-emulator"
PORT=$PORT_LINUX_EMULATOR EMULATOR_CONFIG_PATH="config/linux_config.json" CONTROL_PASSWORD="TestPass123!" .venv/bin/python app.py > "$WORKSPACE_DIR/logs/sysman-emulator-linux.log" 2>&1 &
LINUX_EMULATOR_PID=$!

echo "Starting Jira Emulator on port $PORT_JIRA_EMULATOR..."
PORT=$PORT_JIRA_EMULATOR EMULATOR_CONFIG_PATH="config/jira_config.json" CONTROL_PASSWORD="TestPass123!" .venv/bin/python app.py > "$WORKSPACE_DIR/logs/sysman-emulator-jira.log" 2>&1 &
JIRA_EMULATOR_PID=$!

echo "Starting Confluence Emulator on port $PORT_CONFLUENCE_EMULATOR..."
PORT=$PORT_CONFLUENCE_EMULATOR EMULATOR_CONFIG_PATH="config/confluence_config.json" CONTROL_PASSWORD="TestPass123!" .venv/bin/python app.py > "$WORKSPACE_DIR/logs/sysman-emulator-confluence.log" 2>&1 &
CONFLUENCE_EMULATOR_PID=$!

# 2. Start MCP Server
echo "Starting MCP Server on port $MCP_PORT..."
cd "$WORKSPACE_DIR/sysman-mcp-server"
PORT=$MCP_PORT \
SYSTEM_EMULATORS='{"linux-server-01": "http://127.0.0.1:8081", "jira-app-01": "http://127.0.0.1:8082", "confluence-app-01": "http://127.0.0.1:8083"}' \
CONTROL_PASSWORD="TestPass123!" \
CONTROL_HEADER="X-Control-Password" \
.venv/bin/python server.py > "$WORKSPACE_DIR/logs/sysman-mcp.log" 2>&1 &
MCP_PID=$!

# Wait for MCP server to initialize
sleep 2

# 3. Start Detection Agent
echo "Starting Detection Agent A2A service on port $DETECTION_PORT..."
cd "$WORKSPACE_DIR/sysman-detection-agent"
.venv/bin/python -m uvicorn app.fast_api_app:app --port $DETECTION_PORT > "$WORKSPACE_DIR/logs/sysman-detection.log" 2>&1 &
DETECTION_PID=$!

# 4. Start Diagnosis Agent
echo "Starting Diagnosis Agent A2A service on port $DIAGNOSIS_PORT..."
cd "$WORKSPACE_DIR/sysman-diagnosis-agent"
.venv/bin/python -m uvicorn app.fast_api_app:app --port $DIAGNOSIS_PORT > "$WORKSPACE_DIR/logs/sysman-diagnosis.log" 2>&1 &
DIAGNOSIS_PID=$!

# Warm-up delay for remote agents
echo "Warming up remote agent connections (5s)..."
sleep 5

echo "=============================================="
echo " All services running. Launching Orchestrator Playground..."
echo "=============================================="

cd "$WORKSPACE_DIR/sysman-ops-agent"
agents-cli playground
