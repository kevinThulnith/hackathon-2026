import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"


def print_header(title):
    print(f"\n{'='*50}\n🚀 {title}\n{'='*50}")


# ---------------------------------------------------------
# TEST 1: Initialize Universe
# ---------------------------------------------------------
print_header("TEST 1: Universe Initialization")
response = requests.get(f"{BASE_URL}/universe/")
if response.status_code == 200:
    data = response.json()
    print(f"✅ Success! Loaded {len(data['nodes'])} planets.")
    print("Planets available:", ", ".join(data["nodes"].keys()))
else:
    print("❌ Failed:", response.text)

# ---------------------------------------------------------
# TEST 2: Multi-Hop Route ("Hello world")
# ---------------------------------------------------------
print_header("TEST 2: Routing Packet (Aegis -> Caelum)")
payload = {"origin": "Aegis", "destination": "Caelum", "payload": "Hello world"}
response = requests.post(f"{BASE_URL}/route/", json=payload)
if response.status_code == 200:
    data = response.json()
    print(f"✅ Route Found! Path: {' -> '.join(data['path_taken'])}")
    print(f"⏱️ Total Latency: {data['total_latency_seconds']} seconds")
    print("\n📦 First Hop Codex Translation:")
    print(json.dumps(data["hop_log"][0]["data_translation"], indent=2))
else:
    print("❌ Failed:", response.text)

# ---------------------------------------------------------
# TEST 3: Chaos Test (Kill a Node)
# ---------------------------------------------------------
# Let's kill whatever the second node in the path was
node_to_kill = data["path_taken"][1]
print_header(f"TEST 3: Chaos Mode - Killing Planet '{node_to_kill}'")
kill_payload = {"node_id": node_to_kill, "action": "kill"}
response = requests.post(f"{BASE_URL}/toggle/", json=kill_payload)
print(f"💥 Status: {response.json()['status']}")

# ---------------------------------------------------------
# TEST 4: Reroute Packet (Proving Resilience)
# ---------------------------------------------------------
print_header("TEST 4: Rerouting Packet after Node Death")
response = requests.post(f"{BASE_URL}/route/", json=payload)
if response.status_code == 200:
    new_data = response.json()
    print(f"✅ New Route Found! Path: {' -> '.join(new_data['path_taken'])}")

    if new_data["path_taken"] != data["path_taken"]:
        print("🛡️ SUCCESS: System successfully routed around the dead node!")
    else:
        print("⚠️ WARNING: The path didn't change (Check if alternate routes exist).")
else:
    print("❌ Failed:", response.text)
