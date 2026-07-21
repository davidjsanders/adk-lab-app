---
name: routing-metrics
description: Configure and tune dynamic routing protocol metrics including EIGRP and BGP.
---
# Routing Protocol Metrics

Use this skill to adjust and tune protocol-specific routing weights and metric values.

### Routing Metric Attributes
* `eigrp_metric`: Metric configuration string for EIGRP routes
* `bgp_weight`: Integer weight applied to BGP paths

### Available Actions
* `set_eigrp_metric(metric: str)`: Set the active EIGRP metric
* `set_bgp_weight(weight: int)`: Set the BGP route weight
