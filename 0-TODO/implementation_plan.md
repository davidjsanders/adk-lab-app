# ToDo Implementation Plan: Server-Side Streaming (SSE) & ADK Agent Integration

This implementation plan outlines the architectural steps to upgrade the **Router Fleet Operations Dashboard** and **Router Emulators** to use Server-Sent Events (SSE) streaming, establishing the groundwork for a future Google ADK AI Agent integration.

---

## Architecture Overview (Peer Architecture)

```
                          ┌─────────────────────────────────────┐
                          │     Router Dashboard REST & SSE     │
                          │   (/api/proxy/command & /stream)   │
                          └──────────────────┬──────────────────┘
                                             │
               ┌─────────────────────────────┴─────────────────────────────┐
               │                                                           │
               ▼                                                           ▼
┌─────────────────────────────┐                             ┌─────────────────────────────┐
│   Dashboard UI (Peer 1)     │                             │     ADK Agent (Peer 2)      │
│  - Visual Controls & Cards  │                             │  - Autonomous Reasoner      │
│  - SSE Telemetry EventSource│                             │  - ADK Function Tool Calls  │
│  - Execution Logs Display   │                             │  - SSE Event Stream Monitor │
└─────────────────────────────┘                             └─────────────────────────────┘
```

---

## Task Breakdown

### Phase 1: Container & Concurrency Tuning (Cloud Run Optimization)
- [x] **Thread Pool Expansion**: Update `router-dashboard/Dockerfile` and `router-emulator/Dockerfile` Gunicorn startup commands to specify `--threads 16` to handle persistent SSE HTTP connections without worker starvation.
- [x] **Keep-Alive Configuration**: Ensure timeout settings allow long-running streams with periodic heartbeat frames.

### Phase 2: Router Emulator SSE Emitter (`router-emulator`)
- [x] **Implement `/api/stream`**: Add an SSE endpoint in `router-emulator/app.py` returning `mimetype="text/event-stream"`.
- [x] **Event Generator**: Yielder emitting JSON payload frames when telemetry or LED states change.
- [x] **Heartbeat Frame Generator**: Include 15-second `: ping\n\n` comments to prevent Cloud Run proxy timeouts.

### Phase 3: Dashboard Proxy Stream Multiplexer (`router-dashboard`)
- [x] **Implement `/api/proxy/stream`**: Create a proxy streaming endpoint in `router-dashboard/app.py`.
- [x] **Multi-Router Proxy Handler**: Stream telemetry events from active Cloud Run router services into a unified client SSE feed.
- [x] **Preserve REST Control Endpoints**: Keep `/api/proxy/status`, `/api/proxy/command`, and `/api/routers` intact for tool-calling integration.

### Phase 4: Frontend EventSource Integration (`router-dashboard/static/js/app.js`)
- [x] **EventSource Connection**: Replace polling interval in `app.js` with an `EventSource('/api/proxy/stream')` listener.
- [x] **Dynamic DOM Update Handlers**: Update hardware LCD elements (`STATE`, `UPTIME`, `DEPLOYED`, `REV`) and LED indicators on incoming stream events.
- [x] **Fallback Polling Strategy**: Retain explicit REST polling on connection errors or network reconnection events.

### Phase 5: Peer ADK Agent Integration Blueprint
- [ ] **ADK Agent Tool Definitions**: Define ADK function tools (`get_router_status`, `reset_bgp_peering`, `set_fail_mode`, `redeploy_service`) that invoke backend REST endpoints (`/api/proxy/command`, `/api/proxy/status`).
- [ ] **Agent SSE Stream Subscriber**: Equip the ADK Agent to subscribe to `/api/proxy/stream` for real-time telemetry events (e.g. automatic trigger on BGP fault events).
- [ ] **Peer Action Log Sync**: Ensure actions taken by either peer (Dashboard UI or ADK Agent) log cleanly into backend execution history for unified console visibility.

---

## Verification Plan

### Automated Testing
- [x] Run Python bytecode compilation check across modules:
  ```bash
  python3 -m py_compile router-emulator/app.py router-dashboard/app.py
  ```
- [ ] Validate SSE stream headers and ping frame output using `curl`:
  ```bash
  curl -N -H "Accept: text/event-stream" http://localhost:8090/api/proxy/stream
  ```

### Manual Verification
- [ ] Verify LED indicators flash synchronously with SSE stream events.
- [ ] Confirm no HTTP request spam in browser DevTools Network tab.
- [ ] Confirm Cloud Run deployment completes successfully with `--threads 16`.
