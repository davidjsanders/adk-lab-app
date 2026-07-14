#!/usr/bin/env python3
"""Local smoke test script for Router MCP Server tools."""

from server import (
    get_fleet_summary,
    get_router_status,
    list_router_fleet,
    render_router_card,
    send_router_command,
)


def test_mcp_tools():
    print("=== Testing list_router_fleet() ===")
    fleet = list_router_fleet()
    print("Fleet nodes count:", len(fleet))

    print("\n=== Testing get_fleet_summary(page_size=2) (Parallel Batch Page 1) ===")
    page1 = get_fleet_summary(page_size=2)
    print("Page 1 Summary Result:")
    print("Total Count:", page1.get("total_count"))
    print("Batch Size:", page1.get("page_size"))
    print("Next Page Token:", page1.get("next_page_token"))
    for r in page1.get("routers", []):
        print(f"  - Router {r['router_id']} ({r['name']}): status={r['status']}")

    next_token = page1.get("next_page_token")
    if next_token:
        print(f"\n=== Testing get_fleet_summary(page_size=2, page_token='{next_token}') (Page 2) ===")
        page2 = get_fleet_summary(page_size=2, page_token=next_token)
        print("Page 2 Summary Result:")
        print("Batch Size:", page2.get("page_size"))
        print("Next Page Token:", page2.get("next_page_token"))
        for r in page2.get("routers", []):
            print(f"  - Router {r['router_id']} ({r['name']}): status={r['status']}")

    target_id = "RTR-CAN-EAST-01"

    print(f"\n=== Testing send_router_command with dict parameters ===")
    res_dict = send_router_command(target_id, "SET_LED", parameters={"led": "power", "color": "green"})
    print("Command Response (Dict input):", res_dict)


if __name__ == "__main__":
    test_mcp_tools()
