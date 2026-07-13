# Router Emulator Single Page Web Application

An enterprise network router emulator built with Python Flask and vanilla CSS/JS. It mimics physical router hardware LEDs, provides a command interface protected by custom header authorization, and supports multi-instance deployment to Cloud Run.

---

## Key Features

1. **Physical Chassis Visualizer & LEDs**:
   - Realistic router hardware box with indicators: `POWER`, `ONLINE`, `UPSTREAM`, `LAN 1` to `LAN 4`, `SEND (TX)`, `RECEIVE (RX)`.
   - Supports multi-color indicators (`RED`, `AMBER`, `GREEN`, `OFF`) and dynamic flashing intervals (e.g. traffic bursts, self-test boot sequences).
   - Embedded LCD screen showing realtime device ID, location, purpose, uptime, and BGP operational state.
   - **Standalone Compact View (`/compact` or `/widget`)**: Dedicated lightweight page displaying *only* the router chassis and live LEDs, designed specifically for embedding into multi-router dashboard grids or `<iframe>` containers.

2. **Protected Command Interface**:
   - Commands endpoint (`/api/command`) requires header authorization (`X-Control-Password` or configured header).
   - Built-in operational commands:
     - `power_up`: Power on and initialize active links.
     - `power_down`: Graceful shutdown sequence.
     - `reset` / `reboot`: Initiate full bootup sequence with LED self-tests.
     - `bgp_reset`: Trigger BGP link flap simulation.
     - `send_info` / `simulate_traffic`: High-speed packet transmission LED flash burst.
     - `set_led`: Direct override of individual LED colors and flash rates.

3. **Cloud Run Ready & IAM Protected**:
   - Ready to deploy using multi-stage Docker builds.
   - Strictly deployed with `--no-allow-unauthenticated` to ensure IAM protection.

4. **Multi-Router Emulation**:
   - Deploy separate instances with unique environment variables (`ROUTER_ID`, `ROUTER_LOCATION`, `ROUTER_PURPOSE`, `MANUFACTURER_ID`, `CONTROL_PASSWORD`) to simulate entire router topologies.

---

## Local Setup & Quick Start

Automated execution via `run.sh`:

```bash
./run.sh
```

`run.sh` will automatically:
1. Create a Python virtual environment in `.venv`.
2. Install all required dependencies from `requirements.txt`.
3. Start the Flask server locally on `http://127.0.0.1:8080`.
4. Pipe logs to `run.log`.

---

## HTTP SNMP Emulation

Because Google Cloud Run operates over a single exposed HTTP `$PORT`, SNMP is fully emulated over HTTP endpoints using MIB-II (RFC 1213) standard objects:

- **Full MIB Tree Endpoint**: `GET /api/snmp` or `GET /snmp/walk`
- **Single OID Endpoint**: `GET /snmp/get?oid=1.3.6.1.2.1.1.5.0`

### Example: Walk MIB Objects in `snmpwalk` Text Format
```bash
curl -s "http://127.0.0.1:8080/snmp/walk?format=text"
```

Output:
```text
SNMPv2-MIB::sysDescr.0 = STRING: Router Emulator - CISCO-NEXUS-9000-X (v4.18.2-LTS)
SNMPv2-MIB::sysObjectID.0 = OID: .1.3.6.1.4.1.9.1.1
DISMAN-EVENT-MIB::sysUpTimeInstance = Timeticks: Timeticks: (338) 3s
SNMPv2-MIB::sysContact.0 = STRING: Network Admin <admin@example.com>
SNMPv2-MIB::sysName.0 = STRING: RTR-US-EAST-01
SNMPv2-MIB::sysLocation.0 = STRING: New York Data Center, Rack 14B
IF-MIB::ifNumber.0 = INTEGER: 5
IF-MIB::ifOperStatus.1 = INTEGER: up(1)
```

### Example: Query OID via JSON Output
```bash
curl -s "http://127.0.0.1:8080/snmp/get?oid=1.3.6.1.2.1.1.5.0"
```

---

## Command API Usage

All operational requests must pass the control password in the specified authorization header (`X-Control-Password` by default).

### Example: BGP Link Flap Command
```bash
curl -X POST http://127.0.0.1:8080/api/command \
  -H "X-Control-Password: RouterSecretPass123!" \
  -H "Content-Type: application/json" \
  -d '{ "command": "bgp_reset" }'
```

### Example: Custom LED Override
```bash
curl -X POST http://127.0.0.1:8080/api/command \
  -H "X-Control-Password: RouterSecretPass123!" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "set_led",
    "parameters": {
      "led": "lan1",
      "color": "red"
    }
  }'
```

---

## Cloud Run Deployment Guide

1. Configure `cloudrun.env` with your Google Cloud settings and unique Router configuration:
   ```env
   PROJECT_ID=my-gcp-project
   SERVICE_NAME=router-emulator-us-east
   REGION=us-central1
   ROUTER_ID=RTR-NYC-CORE-01
   ROUTER_LOCATION=New York Data Center, Rack 14B
   CONTROL_PASSWORD=SecurePass987!
   ```

2. Run the deployment script:
   ```bash
   ./deploy.sh
   ```

---

## Simulating Multiple Routers

To build a full emulated topology, execute `deploy.sh` with different `cloudrun.env` configurations or flag overrides:

```bash
# Router 1: NYC Edge Router
SERVICE_NAME=router-nyc ROUTER_ID=RTR-NYC-01 ./deploy.sh

# Router 2: London Core Router
SERVICE_NAME=router-lon ROUTER_ID=RTR-LON-01 ROUTER_LOCATION="London DC" ./deploy.sh
```
