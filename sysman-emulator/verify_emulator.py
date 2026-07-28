import subprocess
import time
import urllib.request
import urllib.error
import json

def test_emulator():
    # Start emulator in background on test port 8085
    print("Starting emulator on port 8085...")
    proc = subprocess.Popen(
        [".venv/bin/python", "app.py"],
        env={"PORT": "8085", "CONTROL_PASSWORD": "TestPass123!"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for startup
    time.sleep(2)
    
    try:
        # 1. Test /health
        print("Testing /health ...")
        resp = urllib.request.urlopen("http://127.0.0.1:8085/health")
        health = json.loads(resp.read().decode('utf-8'))
        print("Health status:", health)
        assert health["status"] == "healthy"
        
        # 2. Test /api/status
        print("Testing /api/status ...")
        resp = urllib.request.urlopen("http://127.0.0.1:8085/api/status")
        status_data = json.loads(resp.read().decode('utf-8'))
        print("Active systems discovered:", [s["system_id"] for s in status_data["systems"]])
        assert len(status_data["systems"]) == 3
        
        # 3. Test /metrics
        print("Testing /metrics ...")
        resp = urllib.request.urlopen("http://127.0.0.1:8085/metrics")
        metrics_text = resp.read().decode('utf-8')
        print("Metrics sample lines:")
        for line in metrics_text.splitlines()[:10]:
            print("  ", line)
        assert "process_down" in metrics_text
        assert "sysman_jvm_heap_mb" in metrics_text
        
        # 4. Test /api/command (Unauthorized)
        print("Testing unauthorized /api/command (should fail with 401) ...")
        req = urllib.request.Request(
            "http://127.0.0.1:8085/api/command",
            data=json.dumps({"system_id": "linux-server-01", "command": "STOP_NODE_EXPORTER"}).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        try:
            urllib.request.urlopen(req)
            raise AssertionError("Should have failed with 401")
        except urllib.error.HTTPError as err:
            print("Received expected error code:", err.code)
            assert err.code == 401
            
        # 5. Test /api/command (Authorized)
        print("Testing authorized STOP_NODE_EXPORTER command ...")
        req_auth = urllib.request.Request(
            "http://127.0.0.1:8085/api/command",
            data=json.dumps({"system_id": "linux-server-01", "command": "STOP_NODE_EXPORTER"}).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "X-Control-Password": "TestPass123!"
            }
        )
        resp = urllib.request.urlopen(req_auth)
        cmd_result = json.loads(resp.read().decode('utf-8'))
        print("Command result:", cmd_result)
        assert cmd_result["status"] == "SUCCESS"
        
        # 6. Verify status of linux-server-01 is now UNHEALTHY (process_down = 0)
        print("Verifying process_down state ...")
        resp = urllib.request.urlopen("http://127.0.0.1:8085/api/status?system_id=linux-server-01")
        linux_status = json.loads(resp.read().decode('utf-8'))
        print("Linux Node status after command:", linux_status["status"], linux_status["metrics"])
        assert linux_status["status"] == "UNHEALTHY"
        assert linux_status["metrics"]["process_down"] == 0
        
        print("\nAll integration tests passed successfully!")
        
    finally:
        print("Stopping emulator process...")
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    test_emulator()
