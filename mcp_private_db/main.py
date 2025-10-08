"""Main MCP server for Private Database with Pinecone backend using HTTP Streamable transport."""

import logging
import os
import uuid
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
    return {"message": "MCP Private Database Server", "version": "1.0.0", "protocol": "mcp-http-streamable"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return PlainTextResponse("OK")


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
