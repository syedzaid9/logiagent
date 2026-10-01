import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'http://127.0.0.1:8000/api/v1'

# Authenticate as Admin
login_req = urllib.request.Request(
    f"{BASE_URL}/auth/login",
    data=json.dumps({"email": "admin@logiagent.io", "password": "LogiAgent2026!"}).encode(),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(login_req) as login_res:
    login_data = json.loads(login_res.read())
    token = login_data["access_token"]

auth_headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

queries = [
    ("Scenario 1", "Where is shipment SHP-1001?"),
    ("Scenario 2", "Show me all delayed shipments."),
    ("Scenario 3", "Which vehicle is available for a 1500 kg shipment?"),
    ("Scenario 4", "Show the driver assigned to SHP-1001."),
    ("Scenario 5", "Calculate the estimated delivery time for SHP-1001."),
    ("Scenario 6", "What is the failed delivery policy?"),
    ("Scenario 7", "How is our fleet performing?"),
]

print("=" * 70)
print("LOGIAGENT END-TO-END VERIFICATION SUITE")
print("=" * 70)

all_passed = True

for tag, q in queries:
    req = urllib.request.Request(
        f"{BASE_URL}/agent/chat",
        data=json.dumps({"message": q}).encode(),
        headers=auth_headers
    )
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    
    tools = data.get("tools_used", [])
    actions = data.get("actions_performed", [])
    response = data.get("response", "")
    latency = data.get("latency_ms", 0)

    is_valid = len(tools) > 0 and len(response) > 50 and len(actions) > 0

    status = "PASS" if is_valid else "FAIL"
    if not is_valid:
        all_passed = False

    print(f"[{status}] {tag}: \"{q}\"")
    print(f"       Tools Called: {tools}")
    print(f"       Actions Trace: {' -> '.join(actions)}")
    print(f"       Response Excerpt: {response[:160].replace(chr(10), ' ')}...")
    print(f"       Latency: {latency} ms")
    print("-" * 70)

print("\nOVERALL TEST SUITE RESULT:", "ALL PASSED (PASS)" if all_passed else "SOME FAILED (FAIL)")
