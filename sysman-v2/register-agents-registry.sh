#!/bin/bash
# Script to manually register local SysMan-v2 sub-agents in Vertex AI Agent Registry.

set -e

# Global ports
JIRA_AGENT_PORT=8006
CONFLUENCE_AGENT_PORT=8007
LINUX_AGENT_PORT=8008

location="us-central1"
project="agentspace-argolis-demo"
sa_impersonate="sysman-ops-sa@agentspace-argolis-demo.iam.gserviceaccount.com"

register_agent_in_registry() {
  local agent_name=$1
  local port=$2

  echo "Fetching agent card for ${agent_name} from port ${port}..."
  local retries=5
  while ! curl -s -f "http://127.0.0.1:${port}/a2a/app/.well-known/agent-card.json" > /dev/null; do
    retries=$((retries - 1))
    if [ "$retries" -le 0 ]; then
      echo "Failed to contact local agent card for ${agent_name} on port ${port}."
      echo "Error: Make sure your local environment is running (using run-local-env.sh) before registering!"
      return 1
    fi
    sleep 2
  done

  local card_content
  card_content=$(curl -s "http://127.0.0.1:${port}/a2a/app/.well-known/agent-card.json")

  echo "Registering ${agent_name} in Agent Registry..."
  gcloud alpha agent-registry services delete "${agent_name}" \
    --location="${location}" \
    --project="${project}" \
    --quiet \
    --impersonate-service-account="${sa_impersonate}" >/dev/null 2>&1 || true

  gcloud alpha agent-registry services create "${agent_name}" \
    --location="${location}" \
    --project="${project}" \
    --display-name="${agent_name}" \
    --description="Dynamically registered local ${agent_name} service" \
    --agent-spec-type="a2a-agent-card" \
    --agent-spec-content="${card_content}" \
    --impersonate-service-account="${sa_impersonate}"
}

register_agent_in_registry "sysman-jira-dev" $JIRA_AGENT_PORT
register_agent_in_registry "sysman-confluence-dev" $CONFLUENCE_AGENT_PORT
register_agent_in_registry "sysman-linux-dev" $LINUX_AGENT_PORT

echo "All agent registrations completed successfully!"
