#!/bin/bash
set -e

PROJECT_ID="agentspace-argolis-demo"
LOCATION="us-central1"
PROVIDER_ID="sysman-oauth"
SCOPES="https://www.googleapis.com/auth/cloud-platform"

# Fetch OAuth credentials JSON from Secret Manager
echo "Retrieving client ID and secret from Secret Manager..."
SECRET_PAYLOAD=$(gcloud secrets versions access 1 --secret="sysman-ua" --project="63466983700")

CLIENT_ID=$(echo "$SECRET_PAYLOAD" | jq -r '.web.client_id')
CLIENT_SECRET=$(echo "$SECRET_PAYLOAD" | jq -r '.web.client_secret')

if [ -z "$CLIENT_ID" ] || [ -z "$CLIENT_SECRET" ] || [ "$CLIENT_ID" == "null" ] || [ "$CLIENT_SECRET" == "null" ]; then
  echo "Error: Failed to parse client ID or secret from Secret Manager payload."
  exit 1
fi

echo "Successfully retrieved OAuth credentials."

# Resilient creation / update sequence
# 1. Try to undelete the connector in case it was in soft-deleted state
echo "Undeleting connector '$PROVIDER_ID' if it was soft-deleted..."
gcloud alpha agent-identity connectors undelete "$PROVIDER_ID" \
  --project="$PROJECT_ID" \
  --location="$LOCATION" \
  --quiet 2>/dev/null || true

# 2. Try to update the connector with correct parameters & scopes
echo "Attempting to update connector configuration..."
if gcloud alpha agent-identity connectors update "$PROVIDER_ID" \
  --project="$PROJECT_ID" \
  --location="$LOCATION" \
  --allowed-scopes="$SCOPES" \
  --three-legged-oauth-client-id="$CLIENT_ID" \
  --three-legged-oauth-client-secret="$CLIENT_SECRET" \
  --three-legged-oauth-authorization-url="https://accounts.google.com/o/oauth2/v2/auth" \
  --three-legged-oauth-token-url="https://oauth2.googleapis.com/token" 2>/dev/null; then
  echo "Connector '$PROVIDER_ID' successfully updated."
else
  # 3. If update fails, it means it doesn't exist. Create it fresh!
  echo "Connector does not exist. Creating new connector '$PROVIDER_ID'..."
  gcloud alpha agent-identity connectors create "$PROVIDER_ID" \
    --project="$PROJECT_ID" \
    --location="$LOCATION" \
    --three-legged-oauth-client-id="$CLIENT_ID" \
    --three-legged-oauth-client-secret="$CLIENT_SECRET" \
    --three-legged-oauth-authorization-url="https://accounts.google.com/o/oauth2/v2/auth" \
    --three-legged-oauth-token-url="https://oauth2.googleapis.com/token" \
    --allowed-scopes="$SCOPES"
  echo "Connector '$PROVIDER_ID' successfully created."
fi

echo ""
echo "========================================================================"
echo "Next step: Run the bindings configuration script to finalize local auth"
echo "and Agent Registry bindings setup:"
echo ""
echo "  ./sysman-common/scripts/configure-auth-bindings.sh"
echo "========================================================================"
