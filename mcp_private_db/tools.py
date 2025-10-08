"""MCP tools implementation for search and fetch operations."""

import logging
from typing import List, Dict, Any
from .config import settings
from .schemas import SearchRequest, SearchResponse, FetchRequest, FetchResponse
from .embedder import embed_text, EmbeddingError
from .pinecone_client import get_pinecone_client, PineconeError
from .utils import clean_text

logger = logging.getLogger(__name__)


async def search(query: str, top_k: int = None) -> Dict[str, Any]:
    """
    Search for documents using text query.
    
    Args:
        query: Search query text
        top_k: Number of results to return (1-25, default from config)
    
    Returns:
        Dictionary with search results containing IDs, scores, and previews
    """
    try:
        # Validate inputs
        if not query or not query.strip():
            return {"results": []}
        
        # Clean the query
        query = clean_text(query.strip())
        if not query:
            return {"results": []}
        
        # Set default top_k if not provided
        if top_k is None:
            top_k = settings.DEFAULT_TOP_K
        
        # Validate top_k bounds
        if not (1 <= top_k <= 25):
            logger.warning(f"top_k {top_k} out of bounds, using default {settings.DEFAULT_TOP_K}")
            top_k = settings.DEFAULT_TOP_K
        
        # Get embedding for the query
        try:
            query_vector = embed_text(query)
        except EmbeddingError as e:
            logger.error(f"Embedding failed: {e}")
            return {"results": []}
        
        # Query Pinecone
        try:
            pinecone_client = get_pinecone_client()
            results = pinecone_client.query(query_vector, top_k)
        except PineconeError as e:
            logger.error(f"Pinecone query failed: {e}")
            return {"results": []}
        
        # Return results
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {"results": []}


async def fetch(object_ids: List[str]) -> Dict[str, Any]:
    """
    Fetch full content for specified document IDs.
    
    Args:
        object_ids: List of document IDs to fetch (1-50)
    
    Returns:
        Dictionary with fetched objects containing full content and metadata
    """
    try:
        # Validate inputs
        if not object_ids:
            return {"objects": []}
        
        # Validate number of IDs
        if not (1 <= len(object_ids) <= 50):
            logger.warning(f"Number of object_ids {len(object_ids)} out of bounds")
            return {"objects": []}
        
        # Clean and validate IDs
        clean_ids = []
        for obj_id in object_ids:
            if obj_id and isinstance(obj_id, str) and obj_id.strip():
                clean_ids.append(obj_id.strip())
        
        if not clean_ids:
            return {"objects": []}
        
        # Fetch from Pinecone
        try:
            pinecone_client = get_pinecone_client()
            objects = pinecone_client.fetch(clean_ids)
        except PineconeError as e:
            logger.error(f"Pinecone fetch failed: {e}")
            return {"objects": []}
        
        # Return objects
        return {"objects": objects}
        
    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        return {"objects": []}
