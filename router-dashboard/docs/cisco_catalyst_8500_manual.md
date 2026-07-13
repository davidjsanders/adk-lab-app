# Cisco Catalyst 8500 Edge Series Hardware & IOS XE Manual

## 1. Overview
The Cisco Catalyst 8500 Series Edge Platforms are high-performance SD-WAN and WAN aggregation routers powered by Cisco's 3rd-Generation **Quantum Flow Processor (QFP)**. Built for enterprise cloud edge, 100G WAN aggregation, and zero-trust SASE deployments, the Catalyst 8500 provides hardware-accelerated encryption and deep telemetry.

---

## 2. Hardware Architecture & Specs

| Component | Base Specification | Upgrade Capability |
| :--- | :--- | :--- |
| **Forwarding Processor** | Cisco QFP 3.0 (Quantum Flow Processor) | Hardware-accelerated IPsec Crypto Engine |
| **System DRAM** | 16 GB DDR4 standard | Expandable to 32 GB or 64 GB |
| **Boot Storage** | 32 GB eUSB Boot Flash | Optional 480 GB NVMe SSD expansion |
| **Fixed Uplinks** | 12 x 1GE/10GE SFP+ ports (C8500-12X) | 4 x 40GE / 100GE QSFP28 Flex Ports (C8500-12X4QC) |
| **Console Connectors** | 1 x RJ-45 Serial (RS-232) + 1 x Micro-USB Console | Micro-USB Type-B Auto-baud detection |

---

## 3. Front Panel LED Decoding

### Chassis System Health LEDs
| LED Label | Color State | Status Description |
| :--- | :--- | :--- |
| **PWR (Power)** | Solid Green | All internal power rails and dual PSUs operating within normal limits |
| | Solid Yellow | Unit powered ON, but one power supply unit has failed or disconnected |
| | OFF | System completely unpowered |
| **STAT (Status)** | Solid Green | Cisco IOS XE image successfully loaded and operational |
| | Solid Yellow | Router stuck in ROMMON (ROM Monitor bootloader) recovery mode |
| | Solid Red | Hardware POST critical fault or kernel panic |
| **LINK (Ethernet)** | Green | Valid 10G/100G optical or copper carrier link detected |
| | Amber | Subslot port administratively enabled, but physical link training failed |

---

## 4. Cisco IOS XE CLI Commands & Monitoring

### Standard Management Interface
```bash
# Privileged Access & Hardware Inventory
Router# show platform
Router# show platform resources
Router# show environment all

# Port Speed & Flex Mode Configuration
Router(config)# hw-module subslot 0/0 mode 100G
Router(config-subslot)# exit

# Interface IP and Routing Setup
Router(config)# interface TenGigabitEthernet0/0/0
Router(config-if)# ip address 192.168.10.1 255.255.255.0
Router(config-if)# no shutdown
```

### Serial Console Cable Pinout (RJ-45 RS-232)
Standard Cisco rollover wiring (Pin 1 to Pin 8 reversed):

| RJ-45 Console Pin | Signal Name | Description |
| :--- | :--- | :--- |
| **Pin 1** | RTS | Request To Send |
| **Pin 2** | DTR | Data Terminal Ready |
| **Pin 3** | TXD | Transmit Data |
| **Pin 4** | GND | Ground |
| **Pin 5** | GND | Ground |
| **Pin 6** | RXD | Receive Data |
| **Pin 7** | DSR | Data Set Ready |
| **Pin 8** | CTS | Clear To Send |

*Serial Terminal Parameters*: **9600 8N1** (9600 Baud, 8 Data Bits, No Parity, 1 Stop Bit, No Flow Control).
