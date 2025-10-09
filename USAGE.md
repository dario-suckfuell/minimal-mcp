# MCP Private Database - Usage Guide

## Overview

Your MCP server is running at: `https://minimal-mcp-production-c2e2.up.railway.app`

This server uses **FastMCP** (like the official OpenAI example) with **SSE transport** - no authentication required!

---

## For OpenAI Deep Research

**Simple Configuration:**
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
        "url": "https://minimal-mcp-production-c2e2.up.railway.app"
      }
    }
  ],
  "instructions": "Use the private database to search for relevant documents"
}
```

**That's it!** No authentication tokens needed.

---

## Available Tools

### 1. `search`
Semantic search in your Pinecone knowledge base using vector similarity.

**Parameters:**
- `query` (string, required): The text query to search for
- `top_k` (integer, optional): Number of results to return (1-25, default 8)

**Returns:** `SearchResultPage` with:
- `id`: Document ID
- `score`: Relevance score (0-1)
- `title`: Document title (if available)
- `snippet`: Preview snippet
- `source`: Document source (if available)

### 2. `fetch`
Retrieve full content for specific document IDs.

**Parameters:**
- `object_ids` (array of strings, required): List of document IDs to fetch (1-50)

**Returns:** List of `FetchResult` objects with:
- `id`: Document ID
- `content`: Full document content
- `metadata`: Document metadata (includes all fields from Pinecone)

---

## Testing

Test the production server:
```bash
python3 test_production.py
```

Test locally:
```bash
python3 test_live.py
```

Or test with curl:
```bash
# Health check
curl https://minimal-mcp-production-c2e2.up.railway.app/health

# Get server info
curl https://minimal-mcp-production-c2e2.up.railway.app/
```

---

## Architecture

### Technology Stack:
- **FastMCP**: Official MCP library from OpenAI
- **Transport**: SSE (Server-Sent Events)
- **Backend**: Pinecone vector database
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)

### How It Works:
1. **Search**: Converts your query to embeddings → Searches Pinecone → Returns top matches
2. **Fetch**: Retrieves full document content from Pinecone by ID

### Configuration:
Server configuration is managed via environment variables in Railway:
- `PINECONE_API_KEY`: Your Pinecone API key
- `PINECONE_INDEX`: Pinecone index name
- `PINECONE_HOST`: Pinecone host URL
- `NAMESPACE`: Pinecone namespace (default: `__default__`)
- `OPENAI_API_KEY`: For generating embeddings
- `EMBEDDING_MODEL`: `text-embedding-3-small`
- `EMBEDDING_DIMENSIONS`: `1536`

---

## Common Issues

### ❌ "No results found"
**Solutions:**
1. Check that your Pinecone index has data
2. Verify `NAMESPACE` environment variable matches your data namespace
3. Confirm `EMBEDDING_DIMENSIONS` is set to `1536`

### ❌ "Connection refused" or "Server not responding"
**Solutions:**
1. Check Railway deployment status
2. Verify environment variables are set correctly
3. Check Railway logs for errors

### ❌ "Embedding failed"
**Solutions:**
1. Verify `OPENAI_API_KEY` is set in Railway
2. Check OpenAI API quota/billing
3. Review Railway logs for specific error

---

## Example Usage

### Research Query Example:
```json
{
  "model": "o4-mini-deep-research",
  "input": "Explain Markov Decision Processes in reinforcement learning",
  "background": true,
  "tools": [
    {
      "type": "web_search_preview"
    },
    {
      "type": "mcp",
      "mcp": {
        "url": "https://minimal-mcp-production-c2e2.up.railway.app"
      }
    }
  ],
  "instructions": "Search the private database for relevant academic content about MDPs and reinforcement learning"
}
```

Deep Research will:
1. Use `search` to find relevant documents about MDPs
2. Use `fetch` to retrieve full content
3. Synthesize information from both web search and your private database

---

## Local Development

Run the server locally:
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (copy from env.example)
cp env.example .env
# Edit .env with your credentials

# Run the server
python -m mcp_private_db.main
```

Server will start on `http://localhost:8000`

---

## Summary

✅ **Simple setup** - No authentication required  
✅ **FastMCP** - Uses official OpenAI library  
✅ **SSE transport** - Compatible with Deep Research  
✅ **Semantic search** - Powered by Pinecone vectors  
✅ **Production ready** - Deployed on Railway  

Just add the MCP URL to your Deep Research configuration and start researching! 🚀
