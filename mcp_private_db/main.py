"""Main MCP server for Private Database with Pinecone backend."""

import logging
import os
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from .config import settings
from .tools import search, fetch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MCP Private Database",
    description="A Private Database MCP server backed by Pinecone for Deep Research integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security setup
security = HTTPBearer(auto_error=False)


def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """Verify Bearer token for API authentication."""
    # If no SECRET_TOKEN is configured, skip authentication
    if not settings.SECRET_TOKEN:
        return "no_auth_required"
    
    # If no credentials provided, raise error
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token
    if credentials.credentials != settings.SECRET_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials.credentials


# Request/Response models
class SearchRequest(BaseModel):
    query: str
    top_k: int = None


class FetchRequest(BaseModel):
    object_ids: list[str]


class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]


# MCP-compatible endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "MCP Private Database Server", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return PlainTextResponse("OK")


@app.get("/tools")
async def list_tools(token: str = Depends(verify_token)):
    """List available MCP tools."""
    return {
        "tools": [
            {
                "name": "search",
                "description": "Search for documents using a text query",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query text"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to return (1-25, default 8)",
                            "minimum": 1,
                            "maximum": 25
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "fetch",
                "description": "Fetch full content for specified document IDs",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "object_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of document IDs to fetch (1-50)",
                            "minItems": 1,
                            "maxItems": 50
                        }
                    },
                    "required": ["object_ids"]
                }
            }
        ]
    }


@app.post("/tools/search")
async def search_tool(request: SearchRequest, token: str = Depends(verify_token)):
    """Search tool endpoint."""
    try:
        result = await search(request.query, request.top_k)
        return result
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/fetch")
async def fetch_tool(request: FetchRequest, token: str = Depends(verify_token)):
    """Fetch tool endpoint."""
    try:
        result = await fetch(request.object_ids)
        return result
    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/call")
async def call_tool(request: ToolCallRequest, token: str = Depends(verify_token)):
    """Generic tool call endpoint for MCP compatibility."""
    try:
        if request.name == "search":
            query = request.arguments.get("query", "")
            top_k = request.arguments.get("top_k")
            result = await search(query, top_k)
            return {"content": [{"type": "text", "text": str(result)}]}
        
        elif request.name == "fetch":
            object_ids = request.arguments.get("object_ids", [])
            result = await fetch(object_ids)
            return {"content": [{"type": "text", "text": str(result)}]}
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {request.name}")
    
    except Exception as e:
        logger.error(f"Tool call failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# SSE endpoint for Deep Research compatibility
@app.get("/sse/")
async def sse_endpoint():
    """SSE endpoint for Deep Research integration."""
    return JSONResponse({
        "message": "SSE endpoint available",
        "tools": ["search", "fetch"],
        "endpoints": {
            "search": "/tools/search",
            "fetch": "/tools/fetch",
            "list_tools": "/tools",
            "call": "/call"
        }
    })


def main():
    """Run the server."""
    import uvicorn
    
    host = os.environ.get("HOST", settings.HOST)
    port = int(os.environ.get("PORT", settings.PORT))
    
    logger.info(f"Starting MCP Private Database server on {host}:{port}")
    logger.info(f"Pinecone index: {settings.PINECONE_INDEX}")
    logger.info(f"Embedding enabled: {settings.ENABLE_EMBEDDING}")
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
