# Cold Start & First-Response Performance Improvement Plan

This document outlines actionable strategies to optimize the startup time and first-response latency for the Router Ops Agent deployed on Cloud Run and Agent Runtime (Agent Engine).

---

## ⚡ 1. Set Minimum Warmer Instances (`min-instances = 1`)

* **Problem**: Deploying with `--min-instances 0` causes Cloud Run / Agent Runtime to scale to zero when idle. The first incoming request incurs a full VM container cold start (image pull + container boot).
* **Action Item**: For production or latency-sensitive deployments, set `--min-instances 1` in `agents-cli deploy`.

---

## 🐢 2. Lazy Initialization & Deferred Module Imports

* **Problem**: `a2a_agent/agent.py` executes heavy package imports (`google-adk`, `vertexai`, `pydantic`, `OpenSSL`, `opentelemetry`) and builds the full `A2A_AGENT` schema at module import time (`A2A_AGENT = get_a2a_agent()`).
* **Action Item**:
  * Defer heavy subagent & tool schema initialization until first execution, or lazy-load modules.
  * Pre-cache / memoize the `AgentCardBuilder` output so `asyncio.run(builder.build())` does not run synchronously on every cold container start.

---

## 🌐 3. Cache GCP Metadata Server Queries

* **Problem**: On startup, helper functions (`get_project_number()`, `get_instance_region()`) make external HTTP requests to the GCP Compute Engine Metadata Server (`http://metadata.google.internal/`).
* **Action Item**:
  * Cache metadata results in memory or load them from environment variables (`GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `PROJECT_NUMBER`) to eliminate HTTP round-trips during container boot.

---

## 🔌 4. Asynchronous MCP Connection Warmup

* **Problem**: Cold starting external MCP server endpoints (`MCP_SERVER_URL`) during initial tool schema registration adds cascading latency to the main agent start.
* **Action Item**:
  * Warm up external MCP client connections asynchronously in the background rather than blocking the primary container startup path.
