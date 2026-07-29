---
name: anomaly-detection
description: Query metrics from systems and detect threshold breaches (e.g. CPU load > 90%, process_down == 0).
---
# Anomaly Detection Skill

Use this skill when tasked with identifying active performance anomalies or system outages.

### Threshold Rules & Outage Criteria
1. **Linux Systems**:
   - Outage: `process_down = 0` (implies `node_exporter` is down). Alert severity is CRITICAL.
   - Resource Alert: `cpu_load_percent > 90.0` or `ram_usage_percent > 90.0`. Alert severity is WARNING.
2. **Jira Servers**:
   - JVM Memory Exhaustion: `jvm_heap_mb` / `jvm_max_heap_mb` > 95% (implies OutOfMemory state). Alert severity is CRITICAL.
   - DB Connection Pool Exhausted: `db_connections` >= `db_pool_max`. Alert severity is CRITICAL.
   - Response Latency: `request_latency_ms > 2000.0` or `error_rate_percent > 5.0`. Alert severity is WARNING.
3. **Confluence Servers**:
   - Synchronizer drop: `websocket_connected = 0` (implies collaborative editor ws down). Alert severity is CRITICAL.
   - Disk space: `attachments_disk_percent >= 90.0`. Alert severity is WARNING.

### Guidelines
- First, call `list_systems` to discover what servers are running.
- For each system, call `get_system_status(system_id)` to review current metrics.
- Compare metrics against the criteria above.
- If any threshold is breached, flag it to the orchestrator as an active alert, showing the value and severity.
- Suggest remediation options based on system instructions.
