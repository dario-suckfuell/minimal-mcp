#!/usr/bin/env python3
"""Test SSE endpoint locally."""

import requests
import json

BASE_URL = "http://localhost:8000"
TOKEN = "test-token"  # For local testing without auth

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}


def test_sse_initialize():
    """Test SSE endpoint with initialize."""
    print("\n" + "="*60)
    print("Testing SSE Endpoint - Initialize")
    print("="*60)
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/sse",
            headers=headers,
            json=payload,
            stream=True
        )
        
        print(f"Status: {response.status_code}")
        print("SSE Stream:")
        
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                print(f"  {decoded_line}")
                
                # Parse data lines
                if decoded_line.startswith("data: "):
                    data = decoded_line[6:]  # Remove "data: " prefix
                    try:
                        parsed = json.loads(data)
                        print(f"  Parsed: {json.dumps(parsed, indent=2)}")
                    except:
                        pass
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_http_streamable_initialize():
    """Test HTTP Streamable endpoint with initialize."""
    print("\n" + "="*60)
    print("Testing HTTP Streamable Endpoint - Initialize")
    print("="*60)
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/mcp",
            headers=headers,
            json=payload
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("LOCAL ENDPOINT TESTS")
    print("="*60)
    print("Make sure the server is running with: uvicorn mcp_private_db.main:app")
    print()
    
    # Test both endpoints
    http_result = test_http_streamable_initialize()
    sse_result = test_sse_initialize()
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"HTTP Streamable (/mcp): {'✅ PASSED' if http_result else '❌ FAILED'}")
    print(f"SSE (/sse): {'✅ PASSED' if sse_result else '❌ FAILED'}")
    print("="*60)

