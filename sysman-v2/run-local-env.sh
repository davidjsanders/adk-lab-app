#!/bin/bash
# Script to stand up all SysMan-v2 local processes and launch agents-cli playground.

set -e

# Base directory setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Standard python path for shared modules
export PYTHONPATH="$WORKSPACE_DIR/sysman-v2/sysman-common:$PYTHONPATH"


# Global ports
PORT_LINUX_EMULATOR=8081
PORT_JIRA_EMULATOR=8082
PORT_CONFLUENCE_EMULATOR=8083
MCP_PORT=8005
JIRA_AGENT_PORT=8006
CONFLUENCE_AGENT_PORT=8007
LINUX_AGENT_PORT=8008

# Clean up any stale port bindings from previous runs first
echo "Cleaning up any stale port bindings (8081, 8082, 8083, 8005, 8006, 8007, 8008, 8080)..."
fuser -k 8081/tcp 8082/tcp 8083/tcp 8005/tcp 8006/tcp 8007/tcp 8008/tcp 8080/tcp >/dev/null 2>&1 || true
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
export JIRA_AGENT_URL="http://127.0.0.1:$JIRA_AGENT_PORT/a2a/app"
export CONFLUENCE_AGENT_URL="http://127.0.0.1:$CONFLUENCE_AGENT_PORT/a2a/app"
export LINUX_AGENT_URL="http://127.0.0.1:$LINUX_AGENT_PORT/a2a/app"

# Bypassing google-auth's gcloud fallback logic by copying ADC to a custom path
DEFAULT_ADC_PATH="$HOME/.config/gcloud/application_default_credentials.json"
TEMP_ADC_PATH="$WORKSPACE_DIR/logs/adc_temp.json"

if [ -f "$DEFAULT_ADC_PATH" ]; then
  mkdir -p "$WORKSPACE_DIR/logs"
  cp "$DEFAULT_ADC_PATH" "$TEMP_ADC_PATH"
  export GOOGLE_APPLICATION_CREDENTIALS="$TEMP_ADC_PATH"
fi

# Clean up variables
LINUX_EMULATOR_PID=""
JIRA_EMULATOR_PID=""
CONFLUENCE_EMULATOR_PID=""
MCP_PID=""
JIRA_AGENT_PID=""
CONFLUENCE_AGENT_PID=""
LINUX_AGENT_PID=""

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
  if [ -n "$JIRA_AGENT_PID" ]; then
    log_tty "Stopping Jira Agent (PID: $JIRA_AGENT_PID)..."
    kill "$JIRA_AGENT_PID" 2>/dev/null || true
  fi
  if [ -n "$CONFLUENCE_AGENT_PID" ]; then
    log_tty "Stopping Confluence Agent (PID: $CONFLUENCE_AGENT_PID)..."
    kill "$CONFLUENCE_AGENT_PID" 2>/dev/null || true
  fi
  if [ -n "$LINUX_AGENT_PID" ]; then
    log_tty "Stopping Linux Agent (PID: $LINUX_AGENT_PID)..."
    kill "$LINUX_AGENT_PID" 2>/dev/null || true
  fi

  log_tty "Cleaning up local port bindings (8081, 8082, 8083, 8005, 8006, 8007, 8008, 8080)..."
  fuser -k 8081/tcp 8082/tcp 8083/tcp 8005/tcp 8006/tcp 8007/tcp 8008/tcp 8080/tcp >/dev/null 2>&1 || true
  rm -f "$WORKSPACE_DIR/logs/adc_temp.json" 2>/dev/null || true

  sleep 1
  log_tty "=============================================="
  log_tty "All services successfully stopped."
  log_tty "=============================================="
}

# Trap exits/interrupts
trap cleanup EXIT INT TERM

echo "=============================================="
echo " Starting SysMan-v2 Operations Local Env"
echo "=============================================="

# Ensure logs directory exists
mkdir -p "$WORKSPACE_DIR/logs"

# 1. Start Emulators
echo "Starting Linux Emulator on port $PORT_LINUX_EMULATOR..."
cd "$WORKSPACE_DIR/sysman-v2/sysman-emulator"
PORT=$PORT_LINUX_EMULATOR EMULATOR_CONFIG_PATH="config/linux_config.json" CONTROL_PASSWORD="TestPass123!" uv run python app.py > "$WORKSPACE_DIR/logs/sysman-v2-emulator-linux.log" 2>&1 &
LINUX_EMULATOR_PID=$!

echo "Starting Jira Emulator on port $PORT_JIRA_EMULATOR..."
cd "$WORKSPACE_DIR/sysman-v2/sysman-emulator"
PORT=$PORT_JIRA_EMULATOR EMULATOR_CONFIG_PATH="config/jira_config.json" CONTROL_PASSWORD="TestPass123!" uv run python app.py > "$WORKSPACE_DIR/logs/sysman-v2-emulator-jira.log" 2>&1 &
JIRA_EMULATOR_PID=$!

echo "Starting Confluence Emulator on port $PORT_CONFLUENCE_EMULATOR..."
cd "$WORKSPACE_DIR/sysman-v2/sysman-emulator"
PORT=$PORT_CONFLUENCE_EMULATOR EMULATOR_CONFIG_PATH="config/confluence_config.json" CONTROL_PASSWORD="TestPass123!" uv run python app.py > "$WORKSPACE_DIR/logs/sysman-v2-emulator-confluence.log" 2>&1 &
CONFLUENCE_EMULATOR_PID=$!

# 2. Start MCP Server
echo "Starting MCP Server on port $MCP_PORT..."
cd "$WORKSPACE_DIR/sysman-v2/sysman-mcp-server"
PORT=$MCP_PORT \
SYSTEM_EMULATORS='{"linux-server-01": "http://127.0.0.1:8081", "jira-app-01": "http://127.0.0.1:8082", "confluence-app-01": "http://127.0.0.1:8083"}' \
CONTROL_PASSWORD="TestPass123!" \
CONTROL_HEADER="X-Control-Password" \
uv run python server.py > "$WORKSPACE_DIR/logs/sysman-v2-mcp.log" 2>&1 &
MCP_PID=$!

# Wait for MCP server to initialize
sleep 6

# 3. Start Sub-Agents
# Ensure the common skills registry directory is configured
export SKILLS_DIR="$WORKSPACE_DIR/sysman-v2/sysman-common/skills"

echo "Starting Jira Agent on port $JIRA_AGENT_PORT..."
cd "$WORKSPACE_DIR/sysman-v2/sysman-agent"
PORT=$JIRA_AGENT_PORT AGENT_ROLE="specialist" AGENT_CONFIG_FILE="jira-prd.json" uv run python -m uvicorn app.fast_api_app:app --host 127.0.0.1 --port $JIRA_AGENT_PORT > "$WORKSPACE_DIR/logs/sysman-v2-agent-jira.log" 2>&1 &
JIRA_AGENT_PID=$!

echo "Starting Confluence Agent on port $CONFLUENCE_AGENT_PORT..."
cd "$WORKSPACE_DIR/sysman-v2/sysman-agent"
PORT=$CONFLUENCE_AGENT_PORT AGENT_ROLE="specialist" AGENT_CONFIG_FILE="confluence-prd.json" uv run python -m uvicorn app.fast_api_app:app --host 127.0.0.1 --port $CONFLUENCE_AGENT_PORT > "$WORKSPACE_DIR/logs/sysman-v2-agent-confluence.log" 2>&1 &
CONFLUENCE_AGENT_PID=$!

echo "Starting Linux Agent on port $LINUX_AGENT_PORT..."
cd "$WORKSPACE_DIR/sysman-v2/sysman-agent"
PORT=$LINUX_AGENT_PORT AGENT_ROLE="specialist" AGENT_CONFIG_FILE="linux-prd.json" uv run python -m uvicorn app.fast_api_app:app --host 127.0.0.1 --port $LINUX_AGENT_PORT > "$WORKSPACE_DIR/logs/sysman-v2-agent-linux.log" 2>&1 &
LINUX_AGENT_PID=$!
# 4. Wait for Specialist Agents to be fully loaded and ready
echo ""
echo "--------------------------------------------------------------------------------"
echo "NOTE: Waiting for sub-agents to be ready is a local fallback requirement."
echo "In local testing, the Orchestrator eagerly fetches Agent Cards via HTTP"
echo "from the sub-agents' endpoints. In production, they are resolved via the"
echo "Agent Registry control plane, removing this startup order dependency."
echo "--------------------------------------------------------------------------------"
echo ""
wait_for_agent() {
  local url=$1
  local name=$2
  local timeout=30
  local count=0
  echo -n "Waiting for $name ($url) to be ready..."
  while ! curl -s --fail "$url/.well-known/agent-card.json" >/dev/null; do
    sleep 1
    count=$((count + 1))
    if [ $count -ge $timeout ]; then
      echo " TIMEOUT!"
      exit 1
    fi
    echo -n "."
  done
  echo " READY!"
}

wait_for_agent "$JIRA_AGENT_URL" "Jira Agent"
wait_for_agent "$CONFLUENCE_AGENT_URL" "Confluence Agent"
wait_for_agent "$LINUX_AGENT_URL" "Linux Agent"

echo "=============================================="
echo " All services running. Launching Orchestrator Playground..."
echo "=============================================="

# Launch playground for the default role (Orchestrator) with service account impersonation
cd "$WORKSPACE_DIR/sysman-v2/sysman-agent"
IMPERSONATE_SA="sysman-ops-sa@agentspace-argolis-demo.iam.gserviceaccount.com" AGENT_ROLE="orchestrator" AGENT_CONFIG_FILE="orchestrator-prd.json" uv run agents-cli playground 2>&1 | tee "$WORKSPACE_DIR/logs/sysman-v2-playground.log"
