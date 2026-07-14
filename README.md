# adk-lab-app
ADK Lab App - Router Fleet Operations Dashboard & Router Emulators

## Running Locally

To launch the local test fleet (3 router emulators + operations dashboard on port 8080):

```bash
./run-routers.sh
```

This will automatically:
- Set up virtual environments and install dependencies for `router-emulator` and `router-dashboard`.
- Spin up **Router 1** (`RTR-LOCAL-18001`) on `http://127.0.0.1:18001`
- Spin up **Router 2** (`RTR-LOCAL-18002`) on `http://127.0.0.1:18002`
- Spin up **Router 3** (`RTR-LOCAL-18003`) on `http://127.0.0.1:18003`
- Spin up **Dashboard** on `http://127.0.0.1:8080`

Press `Ctrl+C` to cleanly terminate all running services.
