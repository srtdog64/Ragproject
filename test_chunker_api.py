import requests
import json

# Test chunker API
base_url = "http://localhost:7001"

print("Testing Chunker API...")
print("-" * 50)

try:
    # Test health
    response = requests.get(f"{base_url}/health")
    print(f"Health Check: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    print()
    
    # Test strategies endpoint
    print("Testing /api/chunkers/strategies...")
    response = requests.get(f"{base_url}/api/chunkers/strategies")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")
    print()
    
    # Test params endpoint
    print("Testing /api/chunkers/params...")
    response = requests.get(f"{base_url}/api/chunkers/params")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")
        
except requests.ConnectionError:
    print("Cannot connect to server. Is it running?")
except Exception as e:
    print(f"Error: {e}")
