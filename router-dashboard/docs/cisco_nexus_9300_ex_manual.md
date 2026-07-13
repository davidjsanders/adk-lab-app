# Cisco Nexus 9300-EX Series Hardware & NX-OS Configuration Manual

## 1. Overview
The Cisco Nexus 9300-EX Series switches are high-density, fixed-configuration data center switches powered by the **Cisco Cloud Scale ASIC**. Designed for cloud-scale infrastructure, they deliver line-rate telemetry, wire-rate security, and flexible port speeds ranging from 100M to 100Gbps.

---

## 2. Hardware Specifications

| Component | Specification |
| :--- | :--- |
| **System Memory (DRAM)** | 24 GB |
| **Storage (SSD)** | 64 GB internal SSD |
| **System Packet Buffer** | 40 MB shared packet buffer |
| **Architecture** | Cisco Cloud Scale ASIC (ASIC-based forwarding) |
| **Management Interfaces** | 1 x RJ-45 Console, 1 x Out-of-band 10/100/1000 Mbps Management, 1 x SFP Port, 1 x USB 3.0 |

### Common Models & Port Density
* **Nexus 93180YC-EX**: 48 x 1/10/25-Gbps Fiber ports + 6 x 40/100-Gbps QSFP28 Uplinks
* **Nexus 93108TC-EX**: 48 x 100M/1/10GBASE-T RJ-45 ports + 6 x 40/100-Gbps QSFP28 Uplinks
* **Nexus 93180LC-EX**: Up to 32 x 40/50-Gbps QSFP+ ports or 18 x 100-Gbps QSFP28 Uplinks

---

## 3. LED Status Indicators

### System & Chassis LEDs
| LED Label | Color State | Operational Meaning |
| :--- | :--- | :--- |
| **BCN (Beacon)** | Flashing Blue | Switch locator beacon activated by operator |
| **STS (Status)** | Solid Green | System fully booted and operational |
| | Solid Amber | System POST / Bootloader initializing |
| | Solid Red | Power fault or critical system error |
| **ENV (Environment)** | Solid Green | All fan trays and power supply modules functioning normally |
| | Solid Amber | At least one fan tray or power supply unit (PSU) failed or missing |

### Port & Uplink Link LEDs
| Color State | Interface Link Status |
| :--- | :--- |
| **Solid Green** | Transceiver detected, port enabled, physical link UP |
| **Solid Amber** | Port administratively shutdown or transceiver absent |
| **Off** | Transceiver present and port enabled, but physical link DOWN |

---

## 4. NX-OS CLI & Command Reference

### Base Configuration Modes
```bash
# Enter Privileged Configuration
switch# configure terminal
switch(config)# hostname RTR-CAN-EAST-01

# Configure Out-of-Band Management Interface
switch(config)# interface mgmt0
switch(config-if)# ip address 10.0.1.50/24
switch(config-if)# no shutdown
```

### Accessing Underlying Linux Bash Shell
Nexus 9300-EX supports direct access to the Linux bash prompt underneath NX-OS:
```bash
# Enable bash shell capability
switch(config)# feature bash-shell

# Spawn root/admin bash environment
switch# run bash
bash-4.3# uname -a
Linux switch 4.1.21-WR7.0.0.12_standard #1 SMP PREEMPT

# Return to standard NX-OS VSH
bash-4.3# exit
switch#
```

---

## 5. Console & Cable Pinouts
* **Baud Rate**: 9600 bps
* **Data Bits**: 8
* **Parity**: None
* **Stop Bits**: 1
* **Flow Control**: None (None/Software)
* **Connector Type**: RJ-45 Serial (EIA/TIA-232)
