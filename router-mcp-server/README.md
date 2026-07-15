# Router Fleet Operations MCP Server (`router-mcp-server`)

Model Context Protocol (MCP) server providing FastMCP tools for AI agents to query fleet telemetry, dispatch hardware control commands, fetch operations logs, run SNMP MIB walks, and render snapshot A2UI cards for router nodes.

---

## Capabilities & Architecture

- **Protocol**: Built on `FastMCP` (serving over Streamable HTTP and SSE).
- **ASGI Entrypoint**: Exposes `app = mcp.http_app()` for production WSGI/ASGI servers (Gunicorn + Uvicorn).
- **Tools**:
  - `list_router_fleet`: Lists all registered fleet router nodes.
  - `get_fleet_summary`: Telemetry summary across fleet nodes with pagination.
  - `get_router_status`: State, uptime, LED maps for a target node.
  - `render_router_card`: A2UI v0.8 card manifest generation.
  - `set_router_led`: Adjust chassis LED indicator lights.
  - `reboot_router`: Triggers POST diagnostic reboot.
  - `inject_bgp_fault`: Failure test fault injection.
  - `reset_bgp_session`: Restores BGP peering session.
  - `fetch_router_logs`: Historical hardware logs query.
  - `run_snmp_walk`: SNMP MIB tree walk.

---

## Local Execution

```bash
# Set up virtual environment and install requirements
uv venv .venv
uv pip install -r requirements.txt --python .venv

# Run locally on port 8000 (HTTP/SSE transport)
.venv/bin/python server.py
```

---

## Cloud Run Deployment (IAM Protected)

Deployment utilizes a **multi-stage Docker build** and strictly enforces **IAM authentication** (`--no-allow-unauthenticated`).

### Deployment Command
```bash
./deploy.sh
```

### Script Environment Overrides
- `GOOGLE_CLOUD_PROJECT`: Target GCP project (default: `adk-lab-app-dev`)
- `GOOGLE_CLOUD_LOCATION`: Target GCP region (default: `us-central1`)
- `REGISTRY_BASE`: Artifact Registry image destination (default: `us-central1-docker.pkg.dev/agentspace-argolis-demo/docker-registry`)
- `SERVICE_NAME`: Cloud Run service name (default: `router-mcp-server`)
