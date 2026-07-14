#!/bin/bash
# Local Execution Script for Router Emulator using uv
# Spins up 3 local router emulator instances on ports 18001, 18002, and 18003 automatically.
# Usage:
#   ./run.sh                  # Launches 3 local routers (ports 18001, 18002, 18003)
#   ./run.sh RTR-ID 8080      # Launches a single router with specific ID and port

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$(cd "${PROJECT_DIR}/.." && pwd)/logs"
mkdir -p "$LOGS_DIR"

cd "$PROJECT_DIR"

echo "--------------------------------------------------------"
echo " Setting up Router Emulator local environment using uv..."
echo " Log Folder: ${LOGS_DIR}"
echo "--------------------------------------------------------"

# 1. Create Python virtual environment if missing using uv
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in .venv using uv..."
    uv venv .venv
fi

# 2. Install requirements using uv
echo "Installing dependencies using uv..."
uv pip install -r requirements.txt --python .venv

if [ -n "$1" ]; then
    # Single router mode
    ARG1="$1"
    ARG2="${2:-}"
    if [[ "$ARG1" =~ ^[0-9]+$ ]]; then
        PORT="$ARG1"
        ROUTER_ID="${ARG2:-RTR-CORE-01}"
    else
        ROUTER_ID="$ARG1"
        PORT="${ARG2:-8080}"
    fi

    echo "--------------------------------------------------------"
    echo " Launching single Router Emulator ($ROUTER_ID) on http://127.0.0.1:$PORT"
    echo " Logs recorded in ${LOGS_DIR}/${ROUTER_ID}.txt"
    echo "--------------------------------------------------------"

    ROUTER_ID="$ROUTER_ID" PORT="$PORT" CONTROL_PASSWORD="mock-local-control-password" .venv/bin/python app.py 2>&1 | tee "${LOGS_DIR}/${ROUTER_ID}.txt"
else
    # Multi-router local cluster mode (3 routers on 18001, 18002, 18003)
    echo "--------------------------------------------------------"
    echo " Launching 3 Local Router Emulators in parallel:"
    echo "   - RTR-LOCAL-18001 on http://127.0.0.1:18001 (Log: logs/RTR-LOCAL-18001.txt)"
    echo "   - RTR-LOCAL-18002 on http://127.0.0.1:18002 (Log: logs/RTR-LOCAL-18002.txt)"
    echo "   - RTR-LOCAL-18003 on http://127.0.0.1:18003 (Log: logs/RTR-LOCAL-18003.txt)"
    echo " Press Ctrl+C to stop all 3 routers."
    echo "--------------------------------------------------------"

    PIDS=()

    cleanup() {
        trap - SIGINT SIGTERM EXIT
        echo ""
        echo "Stopping all local router emulator processes..."
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
        exit 0
    }
    trap cleanup SIGINT SIGTERM EXIT

    ( exec env ROUTER_ID="RTR-LOCAL-18001" PORT=18001 CONTROL_PASSWORD="mock-local-control-password" .venv/bin/python app.py > "${LOGS_DIR}/RTR-LOCAL-18001.txt" 2>&1 ) &
    PIDS+=($!)

    ( exec env ROUTER_ID="RTR-LOCAL-18002" PORT=18002 CONTROL_PASSWORD="mock-local-control-password" .venv/bin/python app.py > "${LOGS_DIR}/RTR-LOCAL-18002.txt" 2>&1 ) &
    PIDS+=($!)

    ( exec env ROUTER_ID="RTR-LOCAL-18003" PORT=18003 CONTROL_PASSWORD="mock-local-control-password" .venv/bin/python app.py > "${LOGS_DIR}/RTR-LOCAL-18003.txt" 2>&1 ) &
    PIDS+=($!)

    echo "Local router processes active (PIDs: ${PIDS[*]})."
    echo "Logs saved in ${LOGS_DIR}/"

    wait
fi
