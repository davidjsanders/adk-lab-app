#!/bin/bash
# Local Execution Script for Router Emulator using uv
# Handles virtual environment setup, package installation, and application launch.

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "--------------------------------------------------------"
echo " Setting up Router Emulator local environment using uv..."
echo "--------------------------------------------------------"

# 1. Create Python virtual environment if missing using uv
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in .venv using uv..."
    uv venv .venv
fi

# 2. Install requirements using uv
echo "Installing dependencies using uv..."
uv pip install -r requirements.txt --python .venv

echo "--------------------------------------------------------"
echo " Launching Router Emulator App on http://127.0.0.1:8080"
echo " Logs recorded in run.log"
echo "--------------------------------------------------------"

# 3. Launch app server logging output to run.log (per Ensure Runnable Deliverables skill)
.venv/bin/python app.py 2>&1 | tee run.log
