# Cisco ASR 9000 Aggregation Services Router Manual

## 1. Overview
The Cisco ASR 9000 Series Aggregation Services Routers (ASR 9010, ASR 9904, etc.) are carrier-class edge and core routers engineered for high-density 100G/400G Ethernet aggregation, BGP border gateway routing, and Service Provider POP networks running **Cisco IOS XR**.

---

## 2. Technical Specifications & Line Cards

| Hardware Component | Details |
| :--- | :--- |
| **Operating System** | Cisco IOS XR 64-bit microkernel architecture |
| **Control Plane (RSP)** | Route Switch Processor 880 (RSP880) with dual multi-core x86 CPUs |
| **Memory** | 32 GB RAM per Route Processor |
| **Forwarding Fabric** | Distributed fabric crossbar up to 400 Gbps per slot |
| **Supported Interfaces** | 10GE (SFP+), 40GE (QSFP+), 100GE (QSFP28), 400GE (QSFP-DD) |

---

## 3. LED Indicators & Diagnostics

| LED Label | State | System Status |
| :--- | :--- | :--- |
| **PWR** | Solid Green | Primary & redundant power modules operating within threshold |
| | Amber | Redundant power supply failure detected |
| **ACT (Active)** | Green | Active Route Switch Processor (RSP) in dual-RSP setup |
| | OFF | Standby RSP in high-availability redundancy mode |
| **FAIL** | Red | Line card initialization fault or fabric error |

---

## 4. Cisco IOS XR Operations & CLI Reference

### Basic Navigation & Administration
```bash
# Enter Admin EXEC mode for chassis supervision
RP/0/RSP0/CPU0:router# admin
RP/0/RSP0/CPU0:router(admin)# show environment

# Commit-based Configuration Workflow
RP/0/RSP0/CPU0:router# configure
RP/0/RSP0/CPU0:router(config)# interface TenGigE0/1/0/0
RP/0/RSP0/CPU0:router(config-if)# ipv4 address 10.100.1.1 255.255.255.0
RP/0/RSP0/CPU0:router(config-if)# no shutdown
RP/0/RSP0/CPU0:router(config-if)# commit
```
