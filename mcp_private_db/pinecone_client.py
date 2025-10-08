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
            from pinecone.grpc import PineconeGRPC as Pinecone
            
            # Initialize Pinecone client
            pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Get the index
            self.index = pc.Index(settings.PINECONE_INDEX)
            logger.info(f"Connected to Pinecone index: {settings.PINECONE_INDEX}")
            
        except ImportError:
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
            
            response = self.index.query(**query_params)
            
            results = []
            # Handle new Pinecone API response format
            matches = response.matches if hasattr(response, 'matches') else response.get("matches", [])
            for match in matches:
                metadata = match.get("metadata", {})
                
                # Extract text for snippet
                text_content = extract_text_from_metadata(metadata, settings.metadata_text_keys_list)
                snippet = create_snippet(text_content) if text_content else None
                
                result = {
                    "id": match["id"],
                    "score": match["score"],
                    "title": metadata.get("title"),
                    "snippet": snippet,
                    "source": metadata.get("source")
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Pinecone query failed: {e}")
            raise PineconeError(f"Query failed: {e}")
    
    def fetch(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch documents by IDs from Pinecone."""
        try:
            fetch_params = {"ids": ids}
            
            # Add namespace if configured
            if settings.NAMESPACE:
                fetch_params["namespace"] = settings.NAMESPACE
            
            response = self.index.fetch(**fetch_params)
            
            objects = []
            # Handle new Pinecone API response format
            vectors = response.vectors if hasattr(response, 'vectors') else response.get("vectors", {})
            for doc_id, record in vectors.items():
                metadata = record.get("metadata", {})
                
                # Extract content from metadata
                content = extract_text_from_metadata(metadata, settings.metadata_text_keys_list)
                if not content:
                    content = ""
                
                # Truncate content if needed
                truncated_content, was_truncated = truncate_content(content, settings.MAX_CONTENT_CHARS)
                
                # Add truncation flag to metadata
                metadata_copy = metadata.copy()
                metadata_copy["truncated"] = was_truncated
                
                obj = {
                    "id": doc_id,
                    "content": truncated_content,
                    "metadata": metadata_copy
                }
                objects.append(obj)
            
            return objects
            
        except Exception as e:
            logger.error(f"Pinecone fetch failed: {e}")
            raise PineconeError(f"Fetch failed: {e}")


# Global client instance
_pinecone_client = None


def get_pinecone_client() -> PineconeClient:
    """Get the global Pinecone client instance."""
    global _pinecone_client
    if _pinecone_client is None:
        _pinecone_client = PineconeClient()
    return _pinecone_client
