#!/bin/bash
# Combined Local Execution Script for Router Emulators & Operations Dashboard
# Launches 3 router emulators (ports 18001, 18002, 18003) and the dashboard on port 8080.
# Logs are automatically created in ~/dev/adk-lab-app/logs/

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EMULATOR_DIR="${BASE_DIR}/router-emulator"
DASHBOARD_DIR="${BASE_DIR}/router-dashboard"
LOGS_DIR="${BASE_DIR}/logs"

mkdir -p "$LOGS_DIR"

echo "========================================================"
echo " Setting up Local Router Fleet Environment (using uv)"
echo " Log Folder: ${LOGS_DIR}"
echo "========================================================"

# Setup router-emulator environment
echo "--> Configuring router-emulator dependencies..."
(
    cd "$EMULATOR_DIR"
    if [ ! -d ".venv" ]; then
        echo "Creating virtual environment in router-emulator/.venv..."
        uv venv .venv
    fi
    uv pip install -r requirements.txt --python .venv
)

# Setup router-dashboard environment
echo "--> Configuring router-dashboard dependencies..."
(
    cd "$DASHBOARD_DIR"
    if [ ! -d ".venv" ]; then
        echo "Creating virtual environment in router-dashboard/.venv..."
        uv venv .venv
    fi
    uv pip install -r requirements.txt --python .venv
)

echo "========================================================"
echo " Launching Local Router Fleet Services:"
echo "   - Router 1   : http://127.0.0.1:18001 (Log: logs/RTR-LOCAL-18001.txt)"
echo "   - Router 2   : http://127.0.0.1:18002 (Log: logs/RTR-LOCAL-18002.txt)"
echo "   - Router 3   : http://127.0.0.1:18003 (Log: logs/RTR-LOCAL-18003.txt)"
echo "   - Dashboard  : http://127.0.0.1:8080      (Log: logs/dashboard.txt)"
echo " Press Ctrl+C to terminate all services."
echo "========================================================"

PIDS=()

cleanup() {
    trap - SIGINT SIGTERM EXIT
    echo ""
    echo "Shutting down local router emulator and dashboard processes..."
    for pid in "${PIDS[@]}"; do
        if [ -n "$pid" ]; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    sleep 0.2
    for pid in "${PIDS[@]}"; do
        if [ -n "$pid" ]; then
            kill -9 "$pid" 2>/dev/null || true
        fi
    done
    pkill -f "ROUTER_ID=RTR-LOCAL" 2>/dev/null || true
    pkill -f "${EMULATOR_DIR}" 2>/dev/null || true
    pkill -f "${DASHBOARD_DIR}" 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 1. Start Router Emulator 1 (Port 18001)
(
    cd "$EMULATOR_DIR"
    exec env ROUTER_ID="RTR-LOCAL-18001" PORT=18001 CONTROL_PASSWORD="mock-local-control-password" .venv/bin/python app.py > "${LOGS_DIR}/RTR-LOCAL-18001.txt" 2>&1
) &
PIDS+=($!)

# 2. Start Router Emulator 2 (Port 18002)
(
    cd "$EMULATOR_DIR"
    exec env ROUTER_ID="RTR-LOCAL-18002" PORT=18002 CONTROL_PASSWORD="mock-local-control-password" .venv/bin/python app.py > "${LOGS_DIR}/RTR-LOCAL-18002.txt" 2>&1
) &
PIDS+=($!)

# 3. Start Router Emulator 3 (Port 18003)
(
    cd "$EMULATOR_DIR"
    exec env ROUTER_ID="RTR-LOCAL-18003" PORT=18003 CONTROL_PASSWORD="mock-local-control-password" .venv/bin/python app.py > "${LOGS_DIR}/RTR-LOCAL-18003.txt" 2>&1
) &
PIDS+=($!)

# 4. Start Router Dashboard (Port 8080)
(
    cd "$DASHBOARD_DIR"
    exec env PORT=8080 .venv/bin/python app.py > "${LOGS_DIR}/dashboard.txt" 2>&1
) &
PIDS+=($!)

echo "Local processes running (PIDs: ${PIDS[*]})"
echo ""

wait
