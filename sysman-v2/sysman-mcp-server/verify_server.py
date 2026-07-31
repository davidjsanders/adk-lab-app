import subprocess
import time
import json
import sys
import os
import re

def send_json_rpc(proc, method, params=None, msg_id=1):
    req = {
        "jsonrpc": "2.0",
        "id": msg_id,
        "method": method,
        "params": params or {}
    }
    req_str = json.dumps(req) + "\n"
    proc.stdin.write(req_str.encode('utf-8'))
    proc.stdin.flush()
    
    # Read response
    resp_line = proc.stdout.readline().decode('utf-8').strip()
    if not resp_line:
        return None
    return json.loads(resp_line)

def test_mcp_server():
    # 1. Start sysman-emulator in background on port 8085
    print("Starting sysman-emulator on port 8085...")
    emulator_dir = os.path.abspath("../sysman-emulator")
    emulator_proc = subprocess.Popen(
        [".venv/bin/python", "app.py"],
        cwd=emulator_dir,
        env={"PORT": "8085", "CONTROL_PASSWORD": "TestPass123!"},
        stdout=subprocess.PIPE,
        stderr=None
    )
    
    # Wait for emulator to be ready
    time.sleep(2.5)
    
    mcp_proc = None
    try:
        # 2. Start sysman-mcp-server in stdio mode
        print("Starting sysman-mcp-server in stdio mode...")
        mcp_proc = subprocess.Popen(
            [".venv/bin/python", "server.py", "--stdio"],
            env={
                "EMULATOR_URL": "http://127.0.0.1:8085",
                "CONTROL_PASSWORD": "TestPass123!",
                "CONTROL_HEADER": "X-Control-Password"
            },
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None
        )
        
        # 3. Send initialize
        print("Sending initialize JSON-RPC request...")
        init_resp = send_json_rpc(mcp_proc, "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        }, msg_id=1)
        print("Initialize response received.")
        assert "result" in init_resp
        
        # Send initialized notification
        req_notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        mcp_proc.stdin.write((json.dumps(req_notif) + "\n").encode('utf-8'))
        mcp_proc.stdin.flush()
        
        # 4. List tools
        print("Sending tools/list request...")
        list_resp = send_json_rpc(mcp_proc, "tools/list", {}, msg_id=2)
        tools = list_resp["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        print("Registered MCP tools:", tool_names)
        assert "list_systems" in tool_names
        assert "get_system_status" in tool_names
        assert "execute_system_command" in tool_names
        assert "render_system_card" in tool_names
        assert "render_system_logs_card" in tool_names
        
        # 5. Call tool list_systems
        print("Calling list_systems tool...")
        call_resp = send_json_rpc(mcp_proc, "tools/call", {
            "name": "list_systems",
            "arguments": {}
        }, msg_id=3)
        result_content = call_resp["result"]["content"]
        # FastMCP wraps output in text block
        result_text = result_content[0]["text"]
        systems = json.loads(result_text)
        print("Active systems from tool:", [s["system_id"] for s in systems])
        assert len(systems) == 3
        
        # 6. Call tool get_system_status for linux-server-01
        print("Calling get_system_status for linux-server-01...")
        status_resp = send_json_rpc(mcp_proc, "tools/call", {
            "name": "get_system_status",
            "arguments": {"system_id": "linux-server-01"}
        }, msg_id=4)
        status_text = status_resp["result"]["content"][0]["text"]
        status_data = json.loads(status_text)
        cpu_metric = next((m for m in status_data["metrics"] if m.get("id") == "cpu_load_percent"), None)
        print("Linux Node CPU:", cpu_metric["value"] if cpu_metric else "N/A")
        assert status_data["status"] == "HEALTHY"
        
        # 7. Call tool render_system_card for jira-app-01
        print("Calling render_system_card for jira-app-01...")
        card_resp = send_json_rpc(mcp_proc, "tools/call", {
            "name": "render_system_card",
            "arguments": {"system_id": "jira-app-01"}
        }, msg_id=5)
        card_text = card_resp["result"]["content"][0]["text"]
        print("Card response contains <a2ui-json> tag format:", "<a2ui-json>" in card_text)
        assert "<a2ui-json>" in card_text
        assert "</a2ui-json>" in card_text
        assert "jira-app-01" in card_text
        
        # 8. Call tool render_system_logs_card for confluence-app-01
        print("Calling render_system_logs_card for confluence-app-01...")
        logs_card_resp = send_json_rpc(mcp_proc, "tools/call", {
            "name": "render_system_logs_card",
            "arguments": {"system_id": "confluence-app-01"}
        }, msg_id=6)
        logs_card_text = logs_card_resp["result"]["content"][0]["text"]
        print("Logs Card response contains <a2ui-json> tag format:", "<a2ui-json>" in logs_card_text)
        assert "<a2ui-json>" in logs_card_text
        assert "</a2ui-json>" in logs_card_text
        assert "confluence-app-01" in logs_card_text
        assert "logs-card-root" in logs_card_text
        
        # 9. Call tool render_system_card for confluence-app-01 to inspect its layout structure
        print("Calling render_system_card for confluence-app-01...")
        conf_card_resp = send_json_rpc(mcp_proc, "tools/call", {
            "name": "render_system_card",
            "arguments": {"system_id": "confluence-app-01"}
        }, msg_id=7)
        conf_card_text = conf_card_resp["result"]["content"][0]["text"]
        # Print the extracted JSON block to see if there are syntax errors or missing IDs
        match = re.search(r"<a2ui-json>(.*?)</a2ui-json>", conf_card_text, re.DOTALL)
        if match:
            print("Confluence Card JSON:\n", match.group(1))
        
        print("\nAll MCP Server integration tests passed successfully!")
        
    finally:
        print("Stopping processes...")
        if mcp_proc:
            mcp_proc.terminate()
            mcp_proc.wait()
        emulator_proc.terminate()
        emulator_proc.wait()

if __name__ == "__main__":
    test_mcp_server()
