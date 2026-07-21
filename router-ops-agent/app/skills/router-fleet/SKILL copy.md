---
name: router-fleet
description: Manage router inventory, device lifecycle (reboot), interface states, and ARP/IP routing tables.
---
# Router Fleet & Interface Management

Use this skill to view, manage, and operate router hardware, interfaces, and baseline IP routing.

### Router & Interface Attributes
* `hostname`
* `interfaces`: Array of network interfaces
  * `interfaces[].ip_address`
  * `interfaces[].netmask`
  * `interfaces[].mac_address`
  * `interfaces[].description`
  * `interfaces[].status`

### Available Actions
* `list_routers()`: List all active routers in the fleet
* `reboot_router(hostname: str)`: Reboot a specific router
* `update_interface_description(hostname: str, interface_name: str, description: str)`: Update interface description
* `add_interface(hostname: str, interface_name: str)`: Add a new interface
* `remove_interface(hostname: str, interface_name: str)`: Remove an interface
* `shutdown_interface(hostname: str, interface_name: str)`: Administratively shut down an interface
* `startup_interface(hostname: str, interface_name: str)`: Bring an interface up
* `show_arp()`: Display ARP table
* `flush_arp()`: Flush the ARP cache
* `show_ip_route()`: Show the IP routing table
* `flush_ip_route()`: Flush the IP routing table

### Example User Interactions
* **Query:** "List all routers."
  * **Response:** "Here are all the routers: <list of routers>"
* **Query:** "Reboot RTR-CAN-EAST-01"
  * **Response:** "Rebooting RTR-CAN-EAST-01..."
