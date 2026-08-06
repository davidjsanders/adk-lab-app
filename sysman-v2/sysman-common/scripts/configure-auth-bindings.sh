#!/bin/bash
set -e

PROJECT_ID="agentspace-argolis-demo"
LOCATION="us-central1"
PROVIDER_ID="sysman-oauth"
TARGET_MCP_URN="urn:mcp:projects-63466983700:projects:63466983700:locations:us-central1:agentregistry:services:common-manager"
IMPERSONATED_SA="sysman-ops-sa@agentspace-argolis-demo.iam.gserviceaccount.com"
BINDING_ID="sysman-mcp-binding"
SCOPES="https://www.googleapis.com/auth/cloud-platform"

# Use a registered agent that already exists in the GCP project as the source agent.
# This satisfies backend validation when creating the binding, allowing local agents
# to dynamically resolve the auth connector.
SOURCE_AGENT_URN="urn:agent:projects-63466983700:projects:63466983700:locations:us-central1:aiplatform:reasoningEngines:9121489640157609984"

# 1. Retrieve current active gcloud user account
CURRENT_ACCOUNT=$(gcloud config get-value account)
if [ -z "$CURRENT_ACCOUNT" ]; then
  echo "Error: No active gcloud account found. Run 'gcloud auth login' first."
  exit 1
fi

echo "Active gcloud account: $CURRENT_ACCOUNT"

# 2. Grant local developer access in Agent Identity Auth Manager using alpha connectors CLI
echo "Granting Connector User permission to developer..."
gcloud alpha agent-identity connectors add-iam-policy-binding "$PROVIDER_ID" \
  --project="$PROJECT_ID" \
  --location="$LOCATION" \
  --role="roles/iamconnectors.user" \
  --member="user:$CURRENT_ACCOUNT"

# 3. Grant the impersonated service account permission (since the local app executes under its context)
echo "Granting Connector User permission to impersonated service account ($IMPERSONATED_SA)..."
gcloud alpha agent-identity connectors add-iam-policy-binding "$PROVIDER_ID" \
  --project="$PROJECT_ID" \
  --location="$LOCATION" \
  --role="roles/iamconnectors.user" \
  --member="serviceAccount:$IMPERSONATED_SA"

# 4. Clean up existing binding if it exists
echo "Cleaning up any existing binding named '$BINDING_ID'..."
gcloud agent-registry bindings delete "$BINDING_ID" \
  --project="$PROJECT_ID" \
  --location="$LOCATION" \
  --quiet || true

# 5. Create Agent Registry binding connecting the registered source agent to the target MCP server
echo "Creating Agent Registry binding linking the MCP server to the auth provider..."
gcloud agent-registry bindings create "$BINDING_ID" \
  --project="$PROJECT_ID" \
  --location="$LOCATION" \
  --display-name="Sysman MCP Auth Binding" \
  --source-identifier="$SOURCE_AGENT_URN" \
  --target-identifier="$TARGET_MCP_URN" \
  --auth-provider-binding="projects/$PROJECT_ID/locations/$LOCATION/connectors/$PROVIDER_ID" \
  --auth-provider-binding-scopes="$SCOPES"

echo "========================================================================"
echo "All outbound auth and agent registry bindings successfully configured!"
echo "========================================================================"
