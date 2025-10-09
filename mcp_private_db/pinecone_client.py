"""Pinecone client wrapper for query and fetch operations."""

import logging
from typing import List, Dict, Any, Optional
from .config import settings
from .utils import extract_text_from_metadata, create_snippet, truncate_content

logger = logging.getLogger(__name__)


class PineconeError(Exception):
    """Custom exception for Pinecone-related errors."""
    pass


class PineconeClient:
    """Wrapper for Pinecone operations."""
    
    def __init__(self):
        self.index = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Pinecone client and index."""
        try:
            # Try the new pinecone package first (v5+)
            try:
                from pinecone import Pinecone
                logger.info("Using Pinecone package (v5+)")
            except ImportError:
                # Fall back to gRPC import for older versions
                from pinecone.grpc import PineconeGRPC as Pinecone
                logger.info("Using Pinecone gRPC package")
            
            # Initialize Pinecone client
            pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Get the index
            self.index = pc.Index(settings.PINECONE_INDEX)
            logger.info(f"Connected to Pinecone index: {settings.PINECONE_INDEX}")
            
        except ImportError as e:
            logger.error(f"Import error: {e}")
            raise PineconeError("Pinecone package not installed. Install with: pip install pinecone")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone client: {e}")
            raise PineconeError(f"Failed to connect to Pinecone: {e}")
    
    def query(self, vector: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Query Pinecone with a vector and return results."""
        try:
            query_params = {
                "vector": vector,
                "top_k": top_k,
                "include_metadata": True,
                "include_values": False
            }
            
            # Add namespace if configured
            if settings.NAMESPACE:
                query_params["namespace"] = settings.NAMESPACE
                logger.info(f"Querying with namespace: {settings.NAMESPACE}")
            else:
                logger.info("Querying without namespace (default namespace)")
            
            logger.info(f"Querying Pinecone with top_k={top_k}, vector_dim={len(vector)}")
            response = self.index.query(**query_params)
            logger.info(f"Pinecone query response type: {type(response)}")
            
            results = []
            # Handle new Pinecone API response format
            matches = response.matches if hasattr(response, 'matches') else response.get("matches", [])
            logger.info(f"Found {len(matches)} matches from Pinecone")
            
            for match in matches:
                # Handle both dict and object response formats
                if hasattr(match, 'metadata'):
                    match_id = match.id
                    match_score = match.score
                    metadata = match.metadata or {}
                else:
                    match_id = match["id"]
                    match_score = match["score"]
                    metadata = match.get("metadata", {})
                
                logger.debug(f"Match: id={match_id}, score={match_score}, metadata_keys={list(metadata.keys())}")
                
                # Extract text for snippet
                text_content = extract_text_from_metadata(metadata, settings.metadata_text_keys_list)
                snippet = create_snippet(text_content) if text_content else None
                
                # Handle metadata access for both dict and object
                title = metadata.get("title") if hasattr(metadata, 'get') else getattr(metadata, 'title', None)
                source = metadata.get("source") if hasattr(metadata, 'get') else getattr(metadata, 'source', None)
                
                result = {
                    "id": match_id,
                    "score": match_score,
                    "title": title,
                    "snippet": snippet,
                    "source": source
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Pinecone query failed: {e}", exc_info=True)
            raise PineconeError(f"Query failed: {e}")
    
    def fetch(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch documents by IDs from Pinecone."""
        try:
            fetch_params = {"ids": ids}
            
            # Add namespace if configured
            if settings.NAMESPACE:
                fetch_params["namespace"] = settings.NAMESPACE
                logger.info(f"Fetching with namespace: {settings.NAMESPACE}")
            else:
                logger.info("Fetching without namespace (default namespace)")
            
            logger.info(f"Fetching {len(ids)} documents from Pinecone: {ids}")
            response = self.index.fetch(**fetch_params)
            
            objects = []
            # Handle new Pinecone API response format
            vectors = response.vectors if hasattr(response, 'vectors') else response.get("vectors", {})
            logger.info(f"Fetch response contains {len(vectors)} vectors")
            
            for doc_id, record in vectors.items():
                # Handle both dict and object response formats
                if hasattr(record, 'metadata'):
                    metadata = record.metadata or {}
                else:
                    metadata = record.get("metadata", {})
                
                logger.debug(f"Fetched doc: id={doc_id}, metadata_keys={list(metadata.keys())}")
                
                # Extract content from metadata
                content = extract_text_from_metadata(metadata, settings.metadata_text_keys_list)
                if not content:
                    content = ""
                    logger.warning(f"No content found for document {doc_id} with metadata keys {list(metadata.keys())}")
                
                # Truncate content if needed
                truncated_content, was_truncated = truncate_content(content, settings.MAX_CONTENT_CHARS)
                
                # Add truncation flag to metadata
                metadata_copy = dict(metadata)  # Convert to dict if it's not already
                metadata_copy["truncated"] = was_truncated
                
                obj = {
                    "id": doc_id,
                    "content": truncated_content,
                    "metadata": metadata_copy
                }
                objects.append(obj)
            
            return objects
            
        except Exception as e:
            logger.error(f"Pinecone fetch failed: {e}", exc_info=True)
            raise PineconeError(f"Fetch failed: {e}")


# Global client instance
_pinecone_client = None


def get_pinecone_client() -> PineconeClient:
    """Get the global Pinecone client instance."""
    global _pinecone_client
    if _pinecone_client is None:
        _pinecone_client = PineconeClient()
    return _pinecone_client
