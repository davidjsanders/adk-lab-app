---
name: router-fleet
description: Manage router inventory, device lifecycle (reboot), interface states, ARP/IP routing tables, and render interactive A2UI router status cards.
---
# Router Fleet & Interface Management

Use this skill to view, manage, and operate router hardware, interfaces, baseline IP routing, and render visual A2UI cards.

### Router & Interface Attributes
* `hostname` / `router_id`
* `interfaces`: Array of network interfaces
  * `interfaces[].ip_address`
  * `interfaces[].netmask`
  * `interfaces[].mac_address`
  * `interfaces[].description`
  * `interfaces[].status`

### Available Actions & Tools
* `list_routers()`: List all active routers in the fleet
* `render_router_card(router_id: str)`: Render an interactive A2UI status dashboard card for a router
* `render_router_card_image(router_id: str)`: Render a PNG snapshot image card
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

### A2UI Rendering Instructions
* Whenever the user asks to view a router status, show a router, display health, or see a card (e.g., "show RTR-CAN-EAST-01", "display router status card"), **ALWAYS invoke `render_router_card(router_id)`**.
* **Strict Verbatim Relay Rule**:
  1. Your ENTIRE response to the user MUST start immediately with `<a2ui-json>` and end with `</a2ui-json>`.
  2. Do NOT include ANY introductory sentence, greeting, or explanation (e.g. "Here is the card:") before or after the `<a2ui-json>` tags.
