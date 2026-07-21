---
name: policy-based-routing
description: Manage and debug Policy-Based Routing (PBR) rules, sequences, and actions.
---
# Policy-Based Routing (PBR) Management

Use this skill to view, configure, edit, enable, disable, and debug Policy-Based Routing rules.

### PBR Rule Attributes
* `rule_id`: Unique identifier of the PBR rule
* `sequence`: Execution order/priority
* `action`: Action to take upon match (e.g., permit, deny, forward)
* `match`: Match criteria (e.g., IP prefix, protocol, port)
* `set`: Next-hop or interface assignment

### Available Actions
* `list_pbr()`: List all active PBR rules
* `add_pbr(rule: str)`: Add a new PBR rule
* `remove_pbr(rule: str)`: Remove an existing PBR rule
* `edit_pbr(rule: str)`: Edit a PBR rule
* `show_pbr_debug(rule: str)`: Show real-time debug information for a PBR rule
* `disable_pbr_rule(rule: str)`: Temporarily disable a PBR rule
* `enable_pbr_rule(rule: str)`: Enable a previously disabled PBR rule
