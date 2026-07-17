# Gemini Enterprise & Agent Runtime Integration Guide

This document captures architecture requirements, routing protocols, and troubleshooting notes for deploying and publishing ADK/A2A agents to **Vertex AI Agent Runtime** and **Gemini Enterprise**.

---

## 🌐 1. The Multi-Protocol Reality in Agent Runtime

When deploying an ADK agent to **Agent Runtime**, the container hosts a unified FastAPI application (`fast_api_app:app`). Different clients and platforms communicate with the agent using different protocols and endpoints:

| Caller / Client | Protocol Used | Endpoint(s) | Purpose |
| :--- | :--- | :--- | :--- |
| **Gemini Enterprise & Cloud Console** | Reasoning Engine RPC | `POST /api/stream_reasoning_engine`<br>`POST /api/reasoning_engine` | Native platform querying, turn streaming, and end-to-end IAM auth. |
| **A2A Clients / External Orchestrators** | A2A JSON-RPC | `POST /a2a/{app_name}`<br>`GET /a2a/{app_name}/.well-known/agent-card.json` | Agent-to-Agent protocol communication and discovery. |
| **ADK CLI / Local Playground** | ADK SSE | `POST /run_sse` | Local debugging, trace streaming, and interactive development. |

---

## 📜 2. The Reasoning Engine Contract (`{class_method, input}`)

When Gemini Enterprise or the Vertex AI Console invokes an agent deployed on Agent Runtime, it does not send raw user prompts or A2A JSON-RPC directly. Instead, the Vertex AI gateway sends an HTTP POST containing a structured wrapper:

```json
{
  "class_method": "async_stream",
  "input": {
    "message": "Show router RTR-CAN-EAST-01",
    "user_id": "user-123",
    "session_id": "session-456"
  }
}
```

The gateway expects the container to handle this request at `/api/stream_reasoning_engine` (for streaming) or `/api/reasoning_engine` (for synchronous execution) and stream back newline-delimited JSON events.

---

## 💥 3. The 404 Endpoint Failure Mode

### Symptom:
When testing a newly published agent in Gemini Enterprise, queries fail immediately with:
> *"Something went wrong while answering your question. Please try again later."*

### Underlying Server Log:
```
INFO: 169.254.169.126:55796 - "POST /api/stream_reasoning_engine HTTP/1.1" 404 Not Found
```

### Root Cause:
During `agents-cli scaffold enhance` or manual code refactoring, conflict resolution may preserve a custom `app/fast_api_app.py` that is missing the adapter hook. Without this hook, FastAPI does not register the `/api/stream_reasoning_engine` route, and all Gemini Enterprise queries return a `404 Not Found`.

---

## 🔌 4. The Solution: `reasoning_engine_adapter.py`

To support Gemini Enterprise and Vertex AI Console alongside native A2A/ADK routes, ensure `app/app_utils/reasoning_engine_adapter.py` is present and mounted in `app/fast_api_app.py`:

```python
from app.app_utils.reasoning_engine_adapter import attach_reasoning_engine_routes

# Initialize FastAPI app
app = get_fast_api_app(...)

# Proxy routes so Vertex AI Console Playground and Gemini Enterprise
# can talk to this agent alongside native routes.
attach_reasoning_engine_routes(app)
```

### What `reasoning_engine_adapter.py` does:
1. **Wraps in `AdkApp`**: Wraps the native ADK `app` inside Vertex AI's `AdkApp` template runtime (`vertexai.agent_engines.templates.adk.AdkApp`).
2. **Shares State**: Connects the shared `SessionService` and `ArtifactService` so session memory remains consistent across A2A, ADK, and Reasoning Engine invocations.
3. **Dispatches Operations**: Unpacks the `{class_method, input}` payload, executes the requested method (e.g., `async_stream`), and streams newline-delimited JSON chunks back to the Gemini Enterprise gateway.

---

## 📋 5. Deployment & Publishing Checklist

When deploying to Agent Runtime and publishing to Gemini Enterprise:

1. **Verify Routes**: Confirm `attach_reasoning_engine_routes(app)` and `attach_a2a_routes(...)` are both present in `app/fast_api_app.py`.
2. **Deploy Container**:
   ```bash
   agents-cli deploy --project PROJECT_ID --region LOCATION --no-confirm-project --update-env-vars "..."
   ```
3. **Publish to Gemini Enterprise**:
   * **ADK Native Mode** (Recommended for Agent Runtime):
     ```bash
     agents-cli publish gemini-enterprise \
       --gemini-enterprise-app-id projects/PROJECT_NUM/locations/LOCATION/collections/default_collection/engines/APP_ID \
       --display-name "My Agent"
     ```
   * **A2A Mode** (Explicit Agent Card URL):
     ```bash
     agents-cli publish gemini-enterprise \
       --registration-type a2a \
       --agent-card-url https://LOCATION-aiplatform.googleapis.com/reasoningEngines/v1/projects/.../api/a2a/app/.well-known/agent-card.json \
       --gemini-enterprise-app-id projects/PROJECT_NUM/locations/LOCATION/collections/default_collection/engines/APP_ID
     ```
