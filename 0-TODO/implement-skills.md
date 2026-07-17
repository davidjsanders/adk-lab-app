# Implementing Skills in ADK & Gemini Enterprise

This document outlines what Skills (`SKILL.md`) are in the ADK and Gemini Enterprise ecosystem, why they are valuable, and how they can be used to scale the capabilities and token efficiency of **Router Agent V2**.

---

## 📖 1. What is a `SKILL.md` File?

A `SKILL.md` file is a structured markdown document that packages procedural knowledge, domain expertise, and operational runbooks for an AI agent. It decouples complex domain instructions from Python code (`app/agent.py`).

### Standard Structure:
```markdown
---
name: bgp_flap_remediation
description: Step-by-step procedure for diagnosing and resetting flapping BGP sessions.
version: 1.0.0
---

# BGP Flap Remediation Skill

## When to Use
Trigger when the user reports BGP state anomalies or when telemetry indicates >5 flaps/hour.

## Pre-requisites & Verification
- Check interface status (`render_router_card`).
- Verify neighbor adjacency state.

## Procedure
1. Check interface counters for packet drops.
2. Run BGP neighbor diagnostics.
3. If flap count exceeds threshold, apply rate-limiting before initiating a session reset.
```

---

## 🎯 2. How Skills Fit into the Ecosystem

1. **In Gemini Enterprise & Google Cloud Console**:
   * The **Overview > Skills** table in the Agent Engine Console lists the advertised capabilities registered on the agent.
   * Higher-level orchestrators and Gemini Enterprise search use these skill metadata fields (`name`, `description`) to discover what specific tasks an agent is qualified to handle.

2. **In ADK Python Agent Code**:
   * Instead of packing all troubleshooting logic into one massive `instruction="..."` string in `app/agent.py`, procedures are organized into a `skills/` directory.

---

## 💡 3. Recommended Use Cases for `router-agent-v2`

As the router fleet agent evolves from telemetry visualization into **active network troubleshooting and remediation**, Skills provide three major architectural benefits:

### A. 🛠️ Modular Troubleshooting Runbooks
Create dedicated skill files for complex, multi-step engineering workflows:
* **`skills/bgp_reset_procedure/SKILL.md`**: Safe BGP session teardown and neighbor adjacency verification.
* **`skills/failover_analysis/SKILL.md`**: Protocol for verifying traffic redirection when a link is degraded.
* **`skills/reboot_safety_checklist/SKILL.md`**: Pre-flight verification checks before executing a hardware reboot.

### B. 📉 Token & Context Optimization
* Large system prompts consume input tokens on **every single turn**.
* With modular skills, the coordinator and diagnostic agents maintain short, concise system instructions. Detailed procedural guides are loaded or referenced only when a matching scenario triggers.

### C. 🤝 Shared Knowledge Across Sub-Agents
* Sub-agents (`diagnostic_agent`, `remediation_agent`) can reference common skills (e.g., *Cisco Nexus vs Juniper Command References*) without duplicating instruction text across Python agent definitions.

---

## 🚀 4. Next Steps for Implementation

1. Create a `skills/` directory at the project root (`app/skills/` or `skills/`).
2. Draft initial runbooks for high-impact router actions (Reboot, BGP Reset, Burst Mode inspection).
3. Connect skill discovery to the agent prompts or ADK toolsets to enable dynamic on-demand retrieval.
