#!/usr/bin/env python3
"""Live test script to verify Pinecone search and fetch functionality."""

import asyncio
import sys
import os

# Add the package to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_private_db.tools import search, fetch
from mcp_private_db.config import settings


async def test_search():
    """Test the search functionality."""
    print("\n" + "="*60)
    print("Testing SEARCH functionality")
    print("="*60)
    
    query = "markov decision process"
    top_k = 5
    
    print(f"\nQuery: '{query}'")
    print(f"Top K: {top_k}")
    print(f"Namespace: {settings.NAMESPACE or '(default)'}")
    print(f"Embedding Model: {settings.EMBEDDING_MODEL}")
    print(f"Embedding Dimensions: {settings.EMBEDDING_DIMENSIONS}")
    
    try:
        result = await search(query, top_k)
        results = result.get("results", [])
        
        print(f"\n✅ Search completed successfully!")
        print(f"Found {len(results)} results\n")
        
        for i, r in enumerate(results, 1):
            print(f"Result {i}:")
            print(f"  ID: {r['id']}")
            print(f"  Score: {r['score']:.4f}")
            print(f"  Title: {r.get('title', 'N/A')}")
            print(f"  Snippet: {r.get('snippet', 'N/A')[:100]}...")
            print()
        
        return results
        
    except Exception as e:
        print(f"\n❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_fetch(doc_id=None):
    """Test the fetch functionality."""
    print("\n" + "="*60)
    print("Testing FETCH functionality")
    print("="*60)
    
    # Use provided ID or the one from your screenshot
    if doc_id is None:
        doc_id = "05211e6d-c272-400f-a528-3530d601a089"
    
    print(f"\nFetching document: {doc_id}")
    print(f"Namespace: {settings.NAMESPACE or '(default)'}")
    
    try:
        result = await fetch([doc_id])
        objects = result.get("objects", [])
        
        print(f"\n✅ Fetch completed successfully!")
        print(f"Retrieved {len(objects)} documents\n")
        
        for obj in objects:
            print(f"Document ID: {obj['id']}")
            print(f"Content length: {len(obj['content'])} characters")
            print(f"Content preview: {obj['content'][:200]}...")
            print(f"Metadata keys: {list(obj['metadata'].keys())}")
            print(f"Truncated: {obj['metadata'].get('truncated', False)}")
            print()
        
        return objects
        
    except Exception as e:
        print(f"\n❌ Fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return []


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("LIVE PINECONE CONNECTION TEST")
    print("="*60)
    print(f"\nPinecone Index: {settings.PINECONE_INDEX}")
    print(f"OpenAI API Key configured: {bool(settings.OPENAI_API_KEY)}")
    
    # Test search first
    search_results = await test_search()
    
    # Test fetch with a known ID
    await test_fetch()
    
    # If search found results, try fetching the first one
    if search_results:
        first_id = search_results[0]['id']
        print("\n" + "="*60)
        print(f"BONUS: Fetching first search result: {first_id}")
        print("="*60)
        await test_fetch(first_id)
    
    print("\n" + "="*60)
    print("Tests completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

