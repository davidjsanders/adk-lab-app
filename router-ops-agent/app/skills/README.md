# Agent Skills Architecture & Progressive Disclosure

This directory houses the modular **Agent Skills** for the Router Operations Agent, adhering to the official **[ADK Skills Standard](https://adk.dev/skills/)**.

---

## 🎯 What Are ADK Agent Skills?

Instead of forcing the LLM to process a monolithic "mega-prompt" containing all possible rules and domain logic on every interaction, **Agent Skills** package instructions, tools, and supporting resources into modular, self-contained directories.

Skills leverage **Progressive Disclosure**:
* **Level 1 (Metadata):** The agent starts with a lightweight system prompt and short skill summaries from the YAML frontmatter.
* **Level 2 (Instructions):** Detailed instructions inside the `SKILL.md` body are fetched by the agent on demand when a user's task matches the skill.
* **Level 3 (Resources):** Optional supporting scripts (`scripts/`), references (`references/`), or assets (`assets/`) bundled inside the skill folder.

---

## 🚀 Key Architectural Benefits

### 1. Token Efficiency & Lower Latency (Reduced Cost)
* **Monolithic Mega-Prompt:** Every turn (even a simple *"Hello"*) pays the token cost and latency penalty for all PBR rules, metric formulas, and interface specifications.
* **SkillToolset Approach:** Only relevant skill instructions are activated during execution, keeping context windows small, fast, and cost-effective.

### 2. Reduced Hallucinations ("Lost in the Middle")
* Overly large prompts with overlapping domain rules (e.g., ARP tables vs. BGP weights vs. PBR sequences) cause attention degradation in LLMs.
* Isolated skills ensure hyper-focused context when the agent is executing specific tasks.

### 3. True Modularity & Zero-Touch Extensibility
* **Plug-and-Play:** To add a new capability (e.g., `bgp-peering`), create a new folder with a `SKILL.md` file under `app/skills/`.
* **Zero Code Churn:** No changes to `agent.py` or `instructions.py` are needed to add, modify, or remove skills.

### 4. Scoped Scripts & Resources
* Skills can bundle their own Python utilities or reference documents. These tools remain scoped to the skill without polluting the global agent namespace.

### 5. Multi-Team Collaboration & Reusability
* Domain teams (Routing, Security, Device Management) can independently develop, test, and version their respective skill folders.
* The exact same skill directory can be reused across different agent projects.

---

## 📁 Directory Structure & Naming Rules

Every skill directory must follow the official ADK naming and structure rules:

```
app/skills/
├── README.md
├── router-fleet/
│   └── SKILL.md
├── policy-based-routing/
│   └── SKILL.md
└── routing-metrics/
    └── SKILL.md
```

### ⚠️ Strict Formatting Requirements
1. **Directory Name:** Must be lowercase **kebab-case** (e.g., `policy-based-routing`).
2. **File Name:** Must be named exactly `SKILL.md` (case-sensitive).
3. **Frontmatter Matching:** The `name:` property in the YAML frontmatter **must strictly match** the directory name.

#### Example `SKILL.md` Structure:
```markdown
---
name: policy-based-routing
description: Manage and debug Policy-Based Routing (PBR) rules, sequences, and actions.
---
# Policy-Based Routing (PBR) Management

Instructions and actions for PBR operations...
```

---

## ⚙️ How Skills Are Loaded in Code

The skills in this folder are automatically discovered by [app/helpers/instructions.py](file:///usr/local/google/home/djsanders/dev/adk-lab-app/router-ops-agent/app/helpers/instructions.py) using the official ADK SDK:

```python
import pathlib
from google.adk.skills import load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset

def get_skill_toolset() -> SkillToolset:
    skills_dir = pathlib.Path(__file__).parent.parent / "skills"
    skills = [
        load_skill_from_dir(p)
        for p in sorted(skills_dir.iterdir())
        if p.is_dir() and (p / "SKILL.md").exists()
    ]
    return SkillToolset(skills=skills)
```

The resulting `SkillToolset` is passed directly to the `Agent(tools=[get_skill_toolset()])` in [app/agent.py](file:///usr/local/google/home/djsanders/dev/adk-lab-app/router-ops-agent/app/agent.py).
