"""MCP server for Private Database with Pinecone backend using FastMCP."""

import logging
from typing import List
from fastmcp.server import FastMCP
from pydantic import BaseModel, Field
from .config import settings
from .tools import search as search_pinecone, fetch as fetch_pinecone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models for responses
class SearchResult(BaseModel):
    """Individual search result."""
    id: str = Field(description="Document ID")
    score: float = Field(description="Relevance score (0-1)")
    title: str | None = Field(None, description="Document title")
    snippet: str | None = Field(None, description="Preview snippet")
    source: str | None = Field(None, description="Document source")


class SearchResultPage(BaseModel):
    """Page of search results."""
    results: List[SearchResult] = Field(description="List of search results")


class FetchResult(BaseModel):
    """Full document result."""
    id: str = Field(description="Document ID")
    content: str = Field(description="Full document content")
    metadata: dict = Field(description="Document metadata")


def create_server():
    """Create and configure the MCP server."""
    mcp = FastMCP(
        name="Private Database MCP",
        instructions=(
            "Search and retrieve documents from a private Pinecone vector database. "
            "Use 'search' to find relevant documents by semantic similarity, "
            "then 'fetch' to retrieve full content."
        )
    )

    @mcp.tool()
    async def search(
        query: str = Field(description="The text query to search for"),
        top_k: int = Field(8, description="Number of results to return (1-25)", ge=1, le=25)
    ) -> SearchResultPage:
        """
        Search for documents using semantic similarity.
        
        Performs vector similarity search in the Pinecone database
        and returns relevant documents with scores and snippets.
        
        Args:
            query: The search query text
            top_k: Number of results to return (default: 8, max: 25)
            
        Returns:
            SearchResultPage with list of matching documents
        """
        try:
            logger.info(f"Search query: '{query}' (top_k={top_k})")
            result = await search_pinecone(query, top_k)
            
            # Convert to Pydantic models
            search_results = [
                SearchResult(
                    id=r["id"],
                    score=r["score"],
                    title=r.get("title"),
                    snippet=r.get("snippet"),
                    source=r.get("source")
                )
                for r in result.get("results", [])
            ]
            
            logger.info(f"Found {len(search_results)} results")
            return SearchResultPage(results=search_results)
            
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            # Return empty results instead of failing
            return SearchResultPage(results=[])

    @mcp.tool()
    async def fetch(
        object_ids: List[str] = Field(description="List of document IDs to fetch (1-50)", min_length=1, max_length=50)
    ) -> List[FetchResult]:
        """
        Fetch full content for specific document IDs.
        
        Retrieves complete document content and metadata from Pinecone
        for the specified document IDs.
        
        Args:
            object_ids: List of document IDs to retrieve (1-50 IDs)
            
        Returns:
            List of FetchResult objects with full content and metadata
        """
        try:
            logger.info(f"Fetching {len(object_ids)} documents")
            result = await fetch_pinecone(object_ids)
            
            # Convert to Pydantic models
            fetch_results = [
                FetchResult(
                    id=obj["id"],
                    content=obj["content"],
                    metadata=obj["metadata"]
                )
                for obj in result.get("objects", [])
            ]
            
            logger.info(f"Retrieved {len(fetch_results)} documents")
            return fetch_results
            
        except Exception as e:
            logger.error(f"Fetch failed: {e}", exc_info=True)
            # Return empty list instead of failing
            return []

    return mcp


def main():
    """Run the MCP server."""
    import os
    
    # Get host and port from environment
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    
    logger.info(f"Starting MCP Private Database server on {host}:{port}")
    logger.info(f"Pinecone index: {settings.PINECONE_INDEX}")
    logger.info(f"Namespace: {settings.NAMESPACE or '(default)'}")
    logger.info(f"Embedding model: {settings.EMBEDDING_MODEL} ({settings.EMBEDDING_DIMENSIONS}D)")
    
    # Create and run the server with SSE transport
    server = create_server()
    server.run(transport="sse", host=host, port=port)


if __name__ == "__main__":
    main()
