# SysMan Operations MCP Server

The **SysMan Operations MCP Server** is a Model Context Protocol (MCP) server built with the [FastMCP](https://github.com/jestlas/fastmcp) framework. It provides agent tools to inspect system health, retrieve application log streams, execute lifecycle commands (reboots, garbage collection, disk purging, fault injections), and render interactive A2UI (Agent-to-User Interface) dashboard/diagnostics cards.

It communicates with modular emulation backends (simulating Jira servers, Confluence nodes, and Linux hosts).

---

## 🛠️ Exposed MCP Tools

The server exposes the following tools to the LLM agent:

| Tool Name | Description | Arguments | Returns |
| :--- | :--- | :--- | :--- |
| `list_systems` | Lists all registered virtual systems in the fleet. | None | `List[SystemMetadata]` |
| `get_system_status` | Queries detailed telemetry metrics, health status, and configurations of a node. | `system_id: str` | `SystemStatus` |
| `execute_system_command` | Executes lifecycle operations, garbage collection, disk purges, or fault injections. | `system_id: str`, `command: str` | `Dict[str, Any]` |
| `get_system_logs` | Retrieves recent syslog or application logs for a system. | `system_id: str`, `limit: int` (default: 15) | `List[LogEntry]` |
| `render_system_card` | Renders an interactive A2UI v0.8 dashboard status card for a node. | `system_id: str` | `str` (enclosed in `<a2ui-json>`) |
| `render_system_logs_card`| Renders an interactive A2UI v0.8 diagnostics logs stream card for a node. | `system_id: str` | `str` (enclosed in `<a2ui-json>`) |

### Supported Lifecycle Commands (for `execute_system_command`)
*   **Linux hosts:** `REBOOT`, `STOP_NODE_EXPORTER`, `START_NODE_EXPORTER`, `INJECT_FAULT`, `CLEAR_FAULT`
*   **Jira servers:** `RESTART_JIRA`, `GC_CLEANUP`, `EXPAND_DB_POOL`, `EXHAUST_DB_POOL`, `TRIGGER_JVM_LEAK`, `RESET_SIMULATION`
*   **Confluence nodes:** `REBOOT`, `RECONNECT_WEBSOCKETS`, `PURGE_ATTACHMENTS`, `DROP_WEBSOCKETS`, `FILL_DISK`, `RESET_SIMULATION`

---

## 🏗️ Architecture

```
sysman-mcp-server/
├── classes/
│   ├── base_card_builder.py   # Abstract builder containing utility methods & template cache
│   ├── card_builder_v08.py    # Concrete orchestrator for A2UI v0.8 card assembly
│   ├── card_builder.py        # CardBuilder proxy routing to concrete versions
│   └── emulator_client.py     # HTTP Client communicating with backend emulators
├── helpers/
│   ├── generate_metrics_components.py # Maps telemetry values to SVG charts and grid layout rows
│   ├── generate_action_components.py  # Dynamically formats control buttons
│   ├── generate_log_components.py     # Colorizes syslog/severity outputs
│   └── clean_payload.py               # Sanitizes A2UI payloads to prevent null key bugs
├── templates/                 # Declarative layout structure JSON templates
│   ├── v08_card_base.json
│   ├── v08_logs_card_base.json
│   └── *.json
└── server.py                  # Entrypoint initializing FastMCP server
```

### Template Caching
The builder implementation decouples structural JSON configuration from executable python code. Templates are loaded dynamically from `/templates` and cached in memory at the class level (`_TEMPLATE_CACHE`) on the first read. This achieves clean code separation with **zero additional disk IO overhead** during high-frequency loops (e.g. log line formatting).

---

## 🚀 Setup and Local Execution

### Prerequisites
*   Python 3.12.3+

### 1. Installation
Create a virtual environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a local `.env` file (or set variables directly in your environment):
```ini
# Port for the MCP server when running in streamable-http mode
PORT=8002

# JSON mapping of system ID to backend emulator URLs
SYSTEM_EMULATORS='{"linux-server-01":"http://127.0.0.1:8085","jira-app-01":"http://127.0.0.1:8086","confluence-app-01":"http://127.0.0.1:8087"}'
```

### 3. Google Cloud Secret Manager Dynamic Authentication
On startup, each emulator node generates a random UUID control password and registers a JSON payload version containing this password to GCP Secret Manager under the secret name: `sysman-emulator-<system_id>`.

Whenever the MCP Server needs to communicate with a target system's emulator, it queries Secret Manager's `latest` version for `sysman-emulator-<system_id>` dynamically. This allows the configuration to survive emulator restarts or scaling events without requiring manual environment adjustments.


### 4. Run the Server
The MCP server supports two transport modes:

*   **Standard I/O Mode (recommended for integration with desktop clients like Claude Desktop):**
    ```bash
    .venv/bin/python server.py --stdio
    ```
*   **Streamable HTTP Mode (runs a local web server):**
    ```bash
    .venv/bin/python server.py
    ```

---

## 🧪 Integration Testing

To verify the integration end-to-end between the MCP server and emulator backends, run:
```bash
.venv/bin/python verify_server.py
```
This validation script:
1. Spins up the `sysman-emulator` background process.
2. Launches `sysman-mcp-server` in stdio mode.
3. Simulates JSON-RPC client handshakes (`initialize`).
4. Invokes core tool routes (`list_systems`, `get_system_status`, `render_system_card`, etc.) and asserts correct status and A2UI tags.
5. Terminates all processes cleanly upon completion.

---

## ☁️ Deployment

Deploy the service to Google Cloud Run by invoking:
```bash
./deploy.sh [PROJECT_ID]
```
The script will build the Docker container using multi-stage builds (optimizing build speed and producing a slim runner containing uvicorn/gunicorn running as a non-root user), push it to your Artifact Registry, and configure identity-based invoker rules.
