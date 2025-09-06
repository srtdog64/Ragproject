#!/usr/bin/env python
"""
Test Ingest functionality with detailed debugging
"""

import requests
import json
import time

def test_ingest():
    """Test document ingestion with detailed output"""
    
    base_url = "http://localhost:7001"
    
    print("="*60)
    print("Testing Document Ingestion")
    print("="*60)
    
    # 1. Check server health
    print("\n1. Checking server health...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"❌ Server returned status: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # 2. Test with simple document
    print("\n2. Testing document ingestion...")
    
    test_doc = {
        "id": "test-001",
        "title": "Test Document",
        "source": "test",
        "text": "This is a test document for checking the ingestion pipeline. It contains some sample text."
    }
    
    print(f"   Document ID: {test_doc['id']}")
    print(f"   Title: {test_doc['title']}")
    print(f"   Text length: {len(test_doc['text'])} chars")
    
    # 3. Send ingest request
    print("\n3. Sending ingest request...")
    
    try:
        response = requests.post(
            f"{base_url}/ingest",
            json={"documents": [test_doc]},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Success!")
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            # Check what was ingested
            if 'ingestedChunks' in data:
                print(f"   Chunks created: {data['ingestedChunks']}")
            if 'documentCount' in data:
                print(f"   Documents processed: {data['documentCount']}")
                
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # 4. Test retrieval to verify ingestion
    print("\n4. Testing retrieval...")
    
    try:
        response = requests.post(
            f"{base_url}/ask",
            json={"question": "test document", "k": 5},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            contexts = data.get('ctxIds', [])
            
            if contexts:
                print(f"   ✅ Found {len(contexts)} contexts")
                print("   Document was successfully ingested and retrieved!")
            else:
                print("   ⚠️ No contexts found")
                print("   Document may not have been properly indexed")
                
        else:
            print(f"   ❌ Retrieval failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Retrieval error: {e}")
    
    print("\n" + "="*60)
    print("Test Complete")
    print("="*60)

if __name__ == "__main__":
    test_ingest()
