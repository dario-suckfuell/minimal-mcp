# MCP Private Database - Usage Guide

## Overview

Your MCP server is running at: `https://minimal-mcp-production-c2e2.up.railway.app`

It provides **two endpoints** for different clients:

## 1. For n8n Agents - HTTP Streamable Endpoint

**Endpoint:** `/mcp`  
**Method:** POST  
**Protocol:** HTTP Streamable (JSON-RPC 2.0)

### n8n Configuration:
```json
{
  "url": "https://minimal-mcp-production-c2e2.up.railway.app/mcp",
  "authorization": {
    "type": "bearer",
    "token": "SOw0R9p0yMp0esPS204MJWcmR9BWm0Pj9M1cLDyapGBcOeI4VCPS8AlR1molXwq7"
  }
}
```

**⚠️ Important:** n8n should use `/mcp` NOT `/sse`

---

## 2. For OpenAI Deep Research - SSE Endpoint

**Endpoint:** `/sse`  
**Methods:** GET (connect) + POST (send commands)  
**Protocol:** Server-Sent Events (SSE)

### OpenAI Deep Research Configuration:
```json
{
  "model": "o4-mini-deep-research",
  "input": "your research question here",
  "background": true,
  "tools": [
    {
      "type": "web_search_preview"
    },
    {
      "type": "mcp",
      "mcp": {
        "url": "https://minimal-mcp-production-c2e2.up.railway.app/sse",
        "authorization": {
          "type": "bearer",
          "token": "SOw0R9p0yMp0esPS204MJWcmR9BWm0Pj9M1cLDyapGBcOeI4VCPS8AlR1molXwq7"
        }
      }
    }
  ],
  "instructions": "Use the private database to search for relevant documents"
}
```

---

## Available Tools

Both endpoints expose the same two MCP tools:

### 1. `search`
Semantic search in your Pinecone knowledge base.

**Parameters:**
- `query` (string, required): The text query to search for
- `top_k` (integer, optional): Number of results to return (1-25, default 8)

**Returns:** List of documents with IDs, scores, and preview snippets

### 2. `fetch`
Retrieve full content for specific document IDs.

**Parameters:**
- `object_ids` (array of strings, required): List of document IDs to fetch (1-50)

**Returns:** Full document content and metadata

---

## Testing

Test the production server:
```bash
python3 test_production_dual.py
```

Test locally:
```bash
python3 test_live.py
```

---

## Common Issues

### ❌ "405 Method Not Allowed"
**Solution:** Make sure you're using the correct endpoint:
- n8n → `/mcp` (POST only)
- OpenAI Deep Research → `/sse` (GET+POST)

### ❌ n8n shows error with SSE
**Solution:** n8n doesn't support SSE. Use `/mcp` endpoint instead.

### ❌ "No results found"
**Solution:** Check that:
1. Your Pinecone index has data
2. `NAMESPACE` environment variable matches your data namespace (or use `__default__`)
3. `EMBEDDING_DIMENSIONS` is set to 1536 (matches your Pinecone index)

---

## Protocol Details

### HTTP Streamable (`/mcp`)
- **Method:** POST
- **Content-Type:** application/json
- **Response:** application/json
- **Use case:** n8n, standard HTTP clients

### SSE (`/sse`)
- **GET:** Establishes SSE connection with heartbeat
- **POST:** Sends MCP commands, returns SSE stream
- **Content-Type:** text/event-stream
- **Use case:** OpenAI Deep Research, SSE clients

Both endpoints use the same JSON-RPC 2.0 protocol underneath!

---

## Summary

✅ **Both protocols work simultaneously**  
✅ **n8n:** Use `/mcp` with POST  
✅ **OpenAI Deep Research:** Use `/sse` with SSE  
✅ **Same tools available on both endpoints**  
✅ **Same authentication for both**

