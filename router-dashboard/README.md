# Global Router Operations Dashboard

A central management and operations web application for monitoring and controlling a fleet of router emulators.

---

## Features

1. **Multi-Router Fleet Visualizer**:
   - Embedded compact hardware LED views for all registered router instances in a responsive grid layout.
   - Shows real-time LED status (`PWR`, `ONLINE`, `UPSTREAM`, `LAN 1-4`, `SEND`, `RECV`), OLED uptime, and router location.

2. **Selected Router Command Console**:
   - Interactive control console allowing operators to select any router node and dispatch commands:
     - `Power Up`
     - `Power Down`
     - `Reboot / Boot Sequence`
     - `BGP Reset`
     - `Simulate Traffic Burst`
     - `Set LED` (Manual override)
     - `SNMP Walk MIB`

3. **Dynamic Router Node Registry**:
   - Add, edit, or remove router instances dynamically via the UI or `routers.json` configuration.
   - Proxies request header authorization (`X-Control-Password`) seamlessly to targeted routers.

4. **Cloud Run Ready & IAM Protected**:
   - Fully deployable to Cloud Run using `deploy.sh` with `--no-allow-unauthenticated`.

---

## Local Setup & Quick Start

Launch the local operations dashboard:

```bash
cd router-dashboard
./run.sh
```

- Dashboard Web App: `http://127.0.0.1:8090`
- Logs saved to: `run.log`

---

## Configuring Router Fleet Nodes

Edit `routers.json` or click `+ Register Router` in the UI header to add router instances:

```json
[
  {
    "id": "RTR-US-EAST-01",
    "name": "US-East Core Router",
    "url": "http://127.0.0.1:8080",
    "location": "New York Data Center, Rack 14B",
    "control_header": "X-Control-Password",
    "control_password": "RouterSecretPass123!"
  },
  {
    "id": "RTR-EU-WEST-01",
    "name": "EU-West Border Gateway",
    "url": "https://router-eu-west-xyz-uc.a.run.app",
    "location": "London Data Center, Cabinet 08A",
    "control_header": "X-Control-Password",
    "control_password": "RouterSecretPass123!"
  }
]
```

---

## Cloud Run Deployment

Configure `cloudrun.env` and execute:

```bash
./deploy.sh
```
