#!/usr/bin/env python3
"""Test both HTTP Streamable and SSE endpoints in production."""

import requests
import json

BASE_URL = "https://minimal-mcp-production-c2e2.up.railway.app"
TOKEN = "SOw0R9p0yMp0esPS204MJWcmR9BWm0Pj9M1cLDyapGBcOeI4VCPS8AlR1molXwq7"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}


def test_http_streamable():
    """Test HTTP Streamable endpoint."""
    print("\n" + "="*60)
    print("Testing HTTP STREAMABLE (/mcp) - for n8n")
    print("="*60)
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/mcp", headers=headers, json=payload)
        print(f"Status: {response.status_code}")
        result = response.json()
        
        if response.status_code == 200 and "result" in result:
            tools = result["result"].get("tools", [])
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool['name']}")
            return True
        else:
            print(f"❌ Error: {result}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_sse():
    """Test SSE endpoint."""
    print("\n" + "="*60)
    print("Testing SSE (/sse) - for OpenAI Deep Research")
    print("="*60)
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/sse",
            headers=headers,
            json=payload,
            stream=True,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("SSE Stream:")
            event_count = 0
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    print(f"  {decoded_line[:100]}")
                    
                    if decoded_line.startswith("data: "):
                        event_count += 1
                        data = decoded_line[6:]
                        try:
                            parsed = json.loads(data)
                            if "result" in parsed:
                                tools = parsed["result"].get("tools", [])
                                print(f"  ✅ Received {len(tools)} tools in SSE event")
                        except:
                            pass
            
            print(f"✅ Received {event_count} SSE events")
            return event_count > 0
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_search_via_sse():
    """Test search tool via SSE."""
    print("\n" + "="*60)
    print("Testing SEARCH via SSE")
    print("="*60)
    
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "search",
            "arguments": {
                "query": "markov decision process",
                "top_k": 3
            }
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/sse",
            headers=headers,
            json=payload,
            stream=True,
            timeout=15
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        data = decoded_line[6:]
                        try:
                            parsed = json.loads(data)
                            if "result" in parsed and "content" in parsed["result"]:
                                content = parsed["result"]["content"]
                                if content and len(content) > 0:
                                    text = content[0].get("text", "")
                                    print(f"✅ Search result preview:\n  {text[:200]}...")
                                    return True
                        except:
                            pass
            
            return False
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("PRODUCTION DUAL-PROTOCOL TEST")
    print("="*60)
    print(f"Testing: {BASE_URL}")
    
    results = {
        "HTTP Streamable (/mcp)": test_http_streamable(),
        "SSE (/sse)": test_sse(),
        "Search via SSE": test_search_via_sse()
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '⚠️  SOME TESTS FAILED'}")
    print("\nUsage:")
    print(f"  n8n:              POST {BASE_URL}/mcp")
    print(f"  OpenAI Deep Research: {BASE_URL}/sse (SSE)")
    print("="*60)

