"""Main MCP server for Private Database with Pinecone backend using HTTP Streamable and SSE transports."""

import logging
import os
import uuid
import json
import asyncio
from typing import Any, Dict, Optional, List, Union
from fastapi import FastAPI, HTTPException, Depends, status, Request, Header
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
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


# MCP Protocol Models
class MCPRequest(BaseModel):
    """Base MCP request model."""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """Base MCP response model."""
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class MCPToolSchema(BaseModel):
    """MCP Tool schema."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


# Session storage (in production, use Redis or similar)
sessions: Dict[str, Dict[str, Any]] = {}


# Helper function to create MCP response
def create_mcp_response(request_id: Optional[Union[str, int]], result: Optional[Dict] = None, error: Optional[Dict] = None) -> Dict:
    """Create MCP-compliant JSON-RPC 2.0 response."""
    response = {
        "jsonrpc": "2.0",
        "id": request_id
    }
    if error:
        response["error"] = error
    else:
        response["result"] = result or {}
    return response


# Public endpoints (no auth required)
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "MCP Private Database Server",
        "version": "1.0.0",
        "protocols": {
            "http_streamable": "/mcp",
            "sse": "/sse"
        },
        "description": "Use /mcp for HTTP Streamable (n8n) or /sse for Server-Sent Events (OpenAI Deep Research)"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return PlainTextResponse("OK")


@app.get("/debug/config")
async def debug_config(token: str = Depends(verify_token)):
    """Debug endpoint to verify configuration (requires auth)."""
    from .pinecone_client import get_pinecone_client
    
    try:
        # Try to get Pinecone client
        pc = get_pinecone_client()
        pinecone_status = "Connected"
        
        # Try to get index stats
        try:
            stats = pc.index.describe_index_stats()
            index_stats = {
                "total_vector_count": stats.total_vector_count if hasattr(stats, 'total_vector_count') else stats.get('total_vector_count', 'unknown'),
                "dimension": stats.dimension if hasattr(stats, 'dimension') else stats.get('dimension', 'unknown'),
                "namespaces": dict(stats.namespaces) if hasattr(stats, 'namespaces') else stats.get('namespaces', {})
            }
        except Exception as e:
            index_stats = {"error": str(e)}
    except Exception as e:
        pinecone_status = f"Error: {str(e)}"
        index_stats = {}
    
    return {
        "config": {
            "pinecone_index": settings.PINECONE_INDEX,
            "namespace": settings.NAMESPACE or "(default)",
            "embedding_enabled": settings.ENABLE_EMBEDDING,
            "embedding_provider": settings.EMBEDDING_PROVIDER,
            "embedding_model": settings.EMBEDDING_MODEL,
            "embedding_dimensions": settings.EMBEDDING_DIMENSIONS,
            "default_top_k": settings.DEFAULT_TOP_K,
            "metadata_text_keys": settings.metadata_text_keys_list,
        },
        "pinecone_status": pinecone_status,
        "index_stats": index_stats,
        "openai_configured": bool(settings.OPENAI_API_KEY)
    }


# MCP HTTP Streamable endpoint
@app.post("/mcp")
async def mcp_endpoint(
    request: Request,
    token: str = Depends(verify_token),
    mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id")
):
    """
    Main MCP HTTP Streamable endpoint.
    Handles all MCP protocol messages according to the JSON-RPC 2.0 spec.
    """
    try:
        body = await request.json()
        
        # Handle single request or batch
        is_batch = isinstance(body, list)
        requests = body if is_batch else [body]
        responses = []
        
        for req_data in requests:
            try:
                mcp_req = MCPRequest(**req_data)
                response = await handle_mcp_request(mcp_req, mcp_session_id)
                responses.append(response)
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                responses.append(create_mcp_response(
                    req_data.get("id"),
                    error={"code": -32600, "message": "Invalid Request", "data": str(e)}
                ))
        
        # Return batch or single response
        result = responses if is_batch else responses[0]
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"MCP endpoint error: {e}")
        return JSONResponse(
            status_code=500,
            content=create_mcp_response(
                None,
                error={"code": -32603, "message": "Internal error", "data": str(e)}
            )
        )


# MCP SSE endpoint for OpenAI Deep Research
@app.post("/sse")
async def mcp_sse_endpoint(
    request: Request,
    token: str = Depends(verify_token),
    mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id")
):
    """
    MCP SSE (Server-Sent Events) endpoint for OpenAI Deep Research.
    Streams MCP protocol messages using SSE format.
    """
    # Read the request body before creating the stream
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse request body: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON in request body"}
        )
    
    return StreamingResponse(
        sse_event_generator(body, mcp_session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


async def sse_event_generator(body: Union[Dict, List], session_id: Optional[str]):
    """Generate SSE events for MCP protocol."""
    try:
        # Handle single request or batch
        is_batch = isinstance(body, list)
        requests = body if is_batch else [body]
        
        for req_data in requests:
            try:
                mcp_req = MCPRequest(**req_data)
                response = await handle_mcp_request(mcp_req, session_id)
                
                # Format as SSE event
                event_data = json.dumps(response)
                yield f"data: {event_data}\n\n"
                
            except Exception as e:
                logger.error(f"Error processing SSE request: {e}")
                error_response = create_mcp_response(
                    req_data.get("id"),
                    error={"code": -32600, "message": "Invalid Request", "data": str(e)}
                )
                yield f"data: {json.dumps(error_response)}\n\n"
        
        # Send done event
        yield "event: done\ndata: {}\n\n"
        
    except Exception as e:
        logger.error(f"SSE stream error: {e}")
        error_response = create_mcp_response(
            None,
            error={"code": -32603, "message": "Internal error", "data": str(e)}
        )
        yield f"data: {json.dumps(error_response)}\n\n"


async def handle_mcp_request(mcp_req: MCPRequest, session_id: Optional[str]) -> Dict:
    """Handle individual MCP request based on method."""
    method = mcp_req.method
    params = mcp_req.params or {}
    
    # Initialize method
    if method == "initialize":
        # Create new session
        if not session_id:
            session_id = str(uuid.uuid4())
        
        sessions[session_id] = {
            "capabilities": params.get("capabilities", {}),
            "clientInfo": params.get("clientInfo", {})
        }
        
        return create_mcp_response(mcp_req.id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": False},
            },
            "serverInfo": {
                "name": "mcp-private-db",
                "version": "1.0.0"
            }
        })
    
    # List tools
    elif method == "tools/list":
        tools = [
            {
                "name": "search",
                "description": "Search for documents using a text query. Returns document IDs, scores, and preview snippets.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The text query to search for"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to return (1-25, default 8)",
                            "default": 8,
                            "minimum": 1,
                            "maximum": 25
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "fetch",
                "description": "Fetch full content and metadata for specified document IDs",
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
        return create_mcp_response(mcp_req.id, {"tools": tools})
    
    # Call tool
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "search":
                query = arguments.get("query", "")
                top_k = arguments.get("top_k")
                result = await search(query, top_k)
                
                # Format as MCP tool response
                return create_mcp_response(mcp_req.id, {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Found {len(result.get('results', []))} documents matching '{query}':\n\n" + 
                                   "\n".join([
                                       f"- {r['id']} (score: {r['score']:.4f}): {r.get('snippet', '')[:100]}"
                                       for r in result.get('results', [])
                                   ])
                        }
                    ],
                    "isError": False
                })
            
            elif tool_name == "fetch":
                object_ids = arguments.get("object_ids", [])
                result = await fetch(object_ids)
                
                # Format as MCP tool response
                objects = result.get('objects', [])
                text_parts = []
                for obj in objects:
                    text_parts.append(f"=== Document: {obj['id']} ===")
                    text_parts.append(f"Content: {obj['content'][:500]}...")
                    text_parts.append(f"Metadata: {obj['metadata']}")
                    text_parts.append("")
                
                return create_mcp_response(mcp_req.id, {
                    "content": [
                        {
                            "type": "text",
                            "text": "\n".join(text_parts)
                        }
                    ],
                    "isError": False
                })
            
            else:
                return create_mcp_response(mcp_req.id, error={
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}"
                })
        
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return create_mcp_response(mcp_req.id, {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error executing tool: {str(e)}"
                    }
                ],
                "isError": True
            })
    
    # Unknown method
    else:
        return create_mcp_response(mcp_req.id, error={
            "code": -32601,
            "message": f"Method not found: {method}"
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
