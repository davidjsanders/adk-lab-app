The "Why" Behind the Difference
This is a known platform limitation tracked internally as GitHub Issue #1916 (b/537292740) 

 . Here is a breakdown of how the two deployment environments handle your agent's UI capabilities:

Aspect	Cloud Run Deployment	Agent Runtime Deployment
Underlying Tech	Docker container hosting an A2A HTTP Server.	Managed Vertex AI ReasoningEngine with AdkApp wrapper 

 .
Registration Pathway	Registered as a2aAgentDefinition with a custom jsonAgentCard 

 .	Registered as adkAgentDefinition by default 

 .
A2UI Rendering Support	Natively Supported (A2UI capabilities are fully advertised in your custom card) 

 .	Blocked/Ignored (The default adkAgentDefinition pathway strips out A2UI headers) 

 .
A2UI Workaround	N/A (Works out of the box).	Register as an a2aAgentDefinition using the Reasoning Engine's auto-exposed A2A endpoint 

 .
 
🛠️ How to Fix It (The Workaround)
To get your A2UI components rendering on Agent Runtime, you must bypass the standard adkAgentDefinition path and register your reasoning engine as an a2aAgentDefinition instead 

 . Here is how you can achieve this:

Step 1: Update your Deployment config
When deploying your agent to Agent Runtime (Reasoning Engine), ensure your config bundles the necessary a2a-sdk requirements so the container can serve the A2A endpoints natively:

python
config = {
    "staging_bucket": f"gs://{PROJECT_ID}",
    "requirements": [
        "google-cloud-aiplatform[agent_engines,adk]",
        "a2a-sdk >= 0.3.5",  # Required for A2A capabilities
    ],
    "http_options": {
        "api_version": "v1beta1",
    }
}
remote_agent = client.agent_engines.create(agent=your_agent, config=config)
Step 2: Register as an a2aAgentDefinition
Any ADK agent deployed to Agent Runtime automatically exposes an A2A-compliant endpoint 

 . Instead of using the adkAgentDefinition payload, register your agent using the a2aAgentDefinition endpoint, pointing the url inside the card directly to the Reasoning Engine's A2A path 

 :

bash
curl -X POST \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "X-Goog-User-Project: YOUR_PROJECT_ID" \
"https://discoveryengine.googleapis.com/v1alpha/projects/YOUR_PROJECT_ID/locations/global/collections/default_collection/engines/YOUR_GEMINI_ENTERPRISE_APP_ID/assistants/default_assistant/agents" \
-d '{
  "displayName": "Your Agent Name",
  "description": "Your Agent Description",
  "a2aAgentDefinition": {
    "jsonAgentCard": "{\"protocolVersion\":\"0.3.0\",\"name\":\"Your Agent\",\"description\":\"My agent deployed on Agent Runtime\",\"url\":\"https://YOUR_REGION-aiplatform.googleapis.com/v1beta1/projects/YOUR_PROJECT_ID/locations/YOUR_REGION/reasoningEngines/YOUR_REASONING_ENGINE_ID/a2a\",\"version\":\"1.0.0\",\"capabilities\":{\"streaming\":false,\"a2ui.org/a2a-extension/a2ui/v0.8\":{\"description\":\"Ability to render A2UI\",\"required\":false,\"params\":{\"supportedCatalogIds\":[\"https://a2ui.org/specification/v0_8/standard_catalog_definition.json\"]}}},\"skills\":[],\"defaultInputModes\":[\"text/plain\"],\"defaultOutputModes\":[\"text/plain\"]}"
  }
}'
⚠️ Note on Streaming: In the current A2A integration on Agent Runtime, streaming is in preview and has known stability issues 

 . Make sure to explicitly set "streaming": false in your jsonAgentCard capabilities block to avoid SSE parsing/snapping issues in the client UI 

 .

🚨 Common Pitfall: Check Your IAM Permissions
Make sure your Discovery Engine service account has the necessary permissions to call your Vertex AI Reasoning Engine. Without these, Gemini Enterprise won't be able to communicate with your agent at all 

 :

Role: Vertex AI User (roles/aiplatform.user) 

 and Vertex AI Viewer (roles/aiplatform.viewer).

Grantee: service-YOUR_PROJECT_NUMBER@gcp-sa-discoveryengine.iam.gserviceaccount.com (Check "Include Google-provided role grants" in the IAM console) 

 .