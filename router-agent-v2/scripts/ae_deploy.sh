#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR/.."

echo "Deploying native A2aAgent to Vertex AI Agent Runtime..."
uv run python scripts/deploy_sdk.py "$@"
