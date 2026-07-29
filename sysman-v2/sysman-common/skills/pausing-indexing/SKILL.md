---
name: pausing-indexing
description: Pause content search indexing to relieve database or CPU pressure.
agent_types: ["Confluence"]
categories: ["SaaS", "on-prem"]
---
# Pausing Indexing Skill

Use this skill when Confluence CPU load is high due to indexing or when pausing index sync is requested.

### Actions
- Check system status and CPU load.
- Pause indexing activity to relieve database and background thread pressure.
- Recommend resuming indexing once the CPU load drops below 80%.
