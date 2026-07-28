#!/bin/bash
# Script to stand up all SysMan local processes and launch agents-cli playground.

set -e

# Base directory setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Global ports
EMULATOR_PORT=8085
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
EMULATOR_PID=""
MCP_PID=""
DETECTION_PID=""
DIAGNOSIS_PID=""

cleanup() {
  echo -e "\n=============================================="
  echo "Shutting down background services..."
  echo "=============================================="
  
  if [ -n "$EMULATOR_PID" ]; then
    kill "$EMULATOR_PID" 2>/dev/null || true
  fi
  if [ -n "$MCP_PID" ]; then
    kill "$MCP_PID" 2>/dev/null || true
  fi
  if [ -n "$DETECTION_PID" ]; then
    kill "$DETECTION_PID" 2>/dev/null || true
  fi
  if [ -n "$DIAGNOSIS_PID" ]; then
    kill "$DIAGNOSIS_PID" 2>/dev/null || true
  fi

  # Wait to allow clean shutdown
  sleep 1
  echo "All services stopped."
}

# Trap exits/interrupts
trap cleanup EXIT INT TERM

echo "=============================================="
echo " Starting SysMan Operations Local Environment"
echo "=============================================="

# Ensure logs directory exists
mkdir -p "$WORKSPACE_DIR/logs"

# 1. Start Emulator
echo "Starting Emulator on port $EMULATOR_PORT..."
cd "$WORKSPACE_DIR/sysman-emulator"
PORT=$EMULATOR_PORT CONTROL_PASSWORD="TestPass123!" .venv/bin/python app.py > "$WORKSPACE_DIR/logs/sysman-emulator.log" 2>&1 &
EMULATOR_PID=$!

# 2. Start MCP Server
echo "Starting MCP Server on port $MCP_PORT..."
cd "$WORKSPACE_DIR/sysman-mcp-server"
PORT=$MCP_PORT \
EMULATOR_URL="http://127.0.0.1:$EMULATOR_PORT" \
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
