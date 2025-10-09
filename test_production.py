#!/usr/bin/env python3
"""Test production MCP endpoint."""

import requests
import json

# Production configuration
MCP_URL = "https://minimal-mcp-production-c2e2.up.railway.app/mcp"
BEARER_TOKEN = "SOw0R9p0yMp0esPS204MJWcmR9BWm0Pj9M1cLDyapGBcOeI4VCPS8AlR1molXwq7"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {BEARER_TOKEN}"
}


def test_initialize():
    """Test MCP initialize."""
    print("\n" + "="*60)
    print("Testing INITIALIZE")
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
    
    response = requests.post(MCP_URL, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_tools_list():
    """Test listing available tools."""
    print("\n" + "="*60)
    print("Testing TOOLS/LIST")
    print("="*60)
    
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response = requests.post(MCP_URL, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if response.status_code == 200 and "result" in result:
        tools = result["result"].get("tools", [])
        print(f"\n✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
    
    return response.status_code == 200


def test_search():
    """Test search tool."""
    print("\n" + "="*60)
    print("Testing SEARCH TOOL")
    print("="*60)
    
    payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "search",
            "arguments": {
                "query": "markov decision process",
                "top_k": 5
            }
        }
    }
    
    print(f"Searching for: 'markov decision process'")
    response = requests.post(MCP_URL, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    
    if response.status_code == 200 and "result" in result:
        content = result["result"].get("content", [])
        if content:
            text = content[0].get("text", "")
            print(f"\n✅ Search result:\n{text}")
            return True
        else:
            print(f"\n❌ No content in response: {json.dumps(result, indent=2)}")
            return False
    else:
        print(f"\n❌ Error response: {json.dumps(result, indent=2)}")
        return False


def test_fetch():
    """Test fetch tool."""
    print("\n" + "="*60)
    print("Testing FETCH TOOL")
    print("="*60)
    
    # Using the ID from the Pinecone screenshot
    doc_id = "05211e6d-c272-400f-a528-3530d601a089"
    
    payload = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "fetch",
            "arguments": {
                "object_ids": [doc_id]
            }
        }
    }
    
    print(f"Fetching document: {doc_id}")
    response = requests.post(MCP_URL, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    
    if response.status_code == 200 and "result" in result:
        content = result["result"].get("content", [])
        if content:
            text = content[0].get("text", "")
            print(f"\n✅ Fetch result (first 500 chars):\n{text[:500]}")
            return True
        else:
            print(f"\n❌ No content in response: {json.dumps(result, indent=2)}")
            return False
    else:
        print(f"\n❌ Error response: {json.dumps(result, indent=2)}")
        return False


def test_debug_config():
    """Test debug config endpoint."""
    print("\n" + "="*60)
    print("Testing DEBUG/CONFIG ENDPOINT")
    print("="*60)
    
    debug_url = "https://minimal-mcp-production-c2e2.up.railway.app/debug/config"
    
    response = requests.get(debug_url, headers={"Authorization": f"Bearer {BEARER_TOKEN}"})
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        config = response.json()
        print(f"\n✅ Configuration:")
        print(json.dumps(config, indent=2))
        return True
    else:
        print(f"\n❌ Error: {response.text}")
        return False


def main():
    """Run all production tests."""
    print("\n" + "="*60)
    print("PRODUCTION MCP SERVER TEST")
    print("="*60)
    print(f"URL: {MCP_URL}")
    print(f"Token: {BEARER_TOKEN[:20]}...")
    
    results = {
        "Initialize": test_initialize(),
        "Tools List": test_tools_list(),
        "Search Tool": test_search(),
        "Fetch Tool": test_fetch(),
        "Debug Config": test_debug_config()
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    print("="*60)


if __name__ == "__main__":
    main()

