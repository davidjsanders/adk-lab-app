#!/usr/bin/env python3
"""Local smoke test script for Router MCP Server tools."""

from server import (
    clone_router,
    delete_router_node,
    get_fleet_summary,
    get_router_status,
    list_router_fleet,
    redeploy_router_node,
    register_or_deploy_router,
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

    print("\n=== Testing MCP Administrative Management Tools ===")
    print("1. Testing clone_router('RTR-CAN-EAST-01' -> 'RTR-TEST-CLONE-01', deploy_cloud_run=False)...")
    clone_res = clone_router("RTR-CAN-EAST-01", "RTR-TEST-CLONE-01", new_name="Test Cloned Local Router", deploy_cloud_run=False)
    print("   Clone Local Result:", clone_res)

    print("2. Testing delete_router_node('RTR-TEST-CLONE-01')...")
    del_res = delete_router_node("RTR-TEST-CLONE-01")
    print("   Delete Local Result:", del_res)

    print("3. Testing clone_router('RTR-CAN-EAST-01' -> 'RTR-CAN-EAST-03', deploy_cloud_run=True)...")
    cr_clone_res = clone_router("RTR-CAN-EAST-01", "RTR-CAN-EAST-03", new_name="Canada East Gateway Router 03", deploy_cloud_run=True)
    print("   Cloud Run Clone Result:", cr_clone_res)

    print("4. Cleaning up test Cloud Run router 'RTR-CAN-EAST-03'...")
    cr_del_res = delete_router_node("RTR-CAN-EAST-03")
    print("   Cloud Run Delete Result:", cr_del_res)


if __name__ == "__main__":
    test_mcp_tools()
