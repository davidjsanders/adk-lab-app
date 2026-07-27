## Cloud Run

```
agents-cli deploy \
  --deployment-target cloud_run \
  --project agentspace-argolis-demo \
  --region us-central1 \
  --service-name roa-cr \
  --service-account router-ops-agent-sa@agentspace-argolis-demo.iam.gserviceaccount.com \
  --cpu 2 \
  --memory 2Gi \
  --min-instances 0 \
  --update-env-vars "GOOGLE_CLOUD_PROJECT=agentspace-argolis-demo,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_GENAI_USE_VERTEXAI=True,MCP_SERVER_URL=https://router-mcp-server-63466983700.us-central1.run.app,DASHBOARD_URL=https://router-dashboard-cta6n7hkya-uc.a.run.app,FAST_MODEL=gemini-3-flash-preview,PRO_MODEL=gemini-3.1-pro-preview" \
  --no-confirm-project

agents-cli publish gemini-enterprise \
  --registration-type a2a \
  --agent-card-url "$(gcloud run services describe roa-cr --project agentspace-argolis-demo --region us-central1 --format='value(status.url)')/a2a/app/.well-known/agent-card.json" \
  --gemini-enterprise-app-id "projects/63466983700/locations/us/collections/default_collection/engines/agentspace-exemplar_1755693787640" \
  --display-name "ROA Router Ops (CRv2)" \
  --deployment-target cloud_run
```

## Agent Engine

```
agents-cli deploy \
  --deployment-target agent_runtime \
  --project agentspace-argolis-demo \
  --region us-central1 \
  --service-name roa-ar \
  --service-account router-ops-agent-sa@agentspace-argolis-demo.iam.gserviceaccount.com \
  --cpu 2 \
  --memory 2Gi \
  --min-instances 0 \
  --update-env-vars "GOOGLE_CLOUD_PROJECT=agentspace-argolis-demo,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_GENAI_USE_VERTEXAI=True,MCP_SERVER_URL=https://router-mcp-server-63466983700.us-central1.run.app,DASHBOARD_URL=https://router-dashboard-cta6n7hkya-uc.a.run.app,FAST_MODEL=gemini-3-flash-preview,PRO_MODEL=gemini-3.1-pro-preview" \
  --no-confirm-project

agents-cli publish gemini-enterprise \
  --registration-type a2a \
  --deployment-target agent_runtime \
  --gemini-enterprise-app-id "projects/63466983700/locations/us/collections/default_collection/engines/agentspace-exemplar_1755693787640" \
  --display-name "ROA Router Ops (ARv2)"
```