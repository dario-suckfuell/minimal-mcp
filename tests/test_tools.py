"""Tests for MCP tools with mocked Pinecone client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from mcp_private_db.tools import search, fetch
from mcp_private_db.config import settings


class TestSearchTool:
    """Test cases for the search tool."""
    
    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        """Test search with empty query returns empty results."""
        result = await search("")
        assert result == {"results": []}
        
        result = await search("   ")
        assert result == {"results": []}
    
    @pytest.mark.asyncio
    async def test_search_valid_query(self):
        """Test search with valid query returns results."""
        mock_results = [
            {
                "id": "doc1",
                "score": 0.95,
                "title": "Test Document",
                "snippet": "This is a test document...",
                "source": "test_source"
            },
            {
                "id": "doc2", 
                "score": 0.87,
                "title": "Another Document",
                "snippet": "Another test document...",
                "source": "test_source"
            }
        ]
        
        with patch('mcp_private_db.tools.embed_text') as mock_embed, \
             patch('mcp_private_db.tools.get_pinecone_client') as mock_client:
            
            mock_embed.return_value = [0.1, 0.2, 0.3]  # Mock embedding vector
            mock_pinecone = Mock()
            mock_pinecone.query.return_value = mock_results
            mock_client.return_value = mock_pinecone
            
            result = await search("test query")
            
            assert result == {"results": mock_results}
            mock_embed.assert_called_once_with("test query")
            mock_pinecone.query.assert_called_once_with([0.1, 0.2, 0.3], settings.DEFAULT_TOP_K)
    
    @pytest.mark.asyncio
    async def test_search_with_custom_top_k(self):
        """Test search with custom top_k parameter."""
        mock_results = [{"id": "doc1", "score": 0.95}]
        
        with patch('mcp_private_db.tools.embed_text') as mock_embed, \
             patch('mcp_private_db.tools.get_pinecone_client') as mock_client:
            
            mock_embed.return_value = [0.1, 0.2, 0.3]
            mock_pinecone = Mock()
            mock_pinecone.query.return_value = mock_results
            mock_client.return_value = mock_pinecone
            
            result = await search("test query", top_k=5)
            
            assert result == {"results": mock_results}
            mock_pinecone.query.assert_called_once_with([0.1, 0.2, 0.3], 5)
    
    @pytest.mark.asyncio
    async def test_search_top_k_bounds(self):
        """Test search with top_k out of bounds uses default."""
        mock_results = [{"id": "doc1", "score": 0.95}]
        
        with patch('mcp_private_db.tools.embed_text') as mock_embed, \
             patch('mcp_private_db.tools.get_pinecone_client') as mock_client:
            
            mock_embed.return_value = [0.1, 0.2, 0.3]
            mock_pinecone = Mock()
            mock_pinecone.query.return_value = mock_results
            mock_client.return_value = mock_pinecone
            
            # Test top_k too high
            result = await search("test query", top_k=100)
            mock_pinecone.query.assert_called_with([0.1, 0.2, 0.3], settings.DEFAULT_TOP_K)
            
            # Test top_k too low
            result = await search("test query", top_k=0)
            mock_pinecone.query.assert_called_with([0.1, 0.2, 0.3], settings.DEFAULT_TOP_K)
    
    @pytest.mark.asyncio
    async def test_search_embedding_error(self):
        """Test search handles embedding errors gracefully."""
        with patch('mcp_private_db.tools.embed_text') as mock_embed:
            mock_embed.side_effect = Exception("Embedding failed")
            
            result = await search("test query")
            assert result == {"results": []}
    
    @pytest.mark.asyncio
    async def test_search_pinecone_error(self):
        """Test search handles Pinecone errors gracefully."""
        with patch('mcp_private_db.tools.embed_text') as mock_embed, \
             patch('mcp_private_db.tools.get_pinecone_client') as mock_client:
            
            mock_embed.return_value = [0.1, 0.2, 0.3]
            mock_client.side_effect = Exception("Pinecone error")
            
            result = await search("test query")
            assert result == {"results": []}


class TestFetchTool:
    """Test cases for the fetch tool."""
    
    @pytest.mark.asyncio
    async def test_fetch_empty_ids(self):
        """Test fetch with empty ID list returns empty results."""
        result = await fetch([])
        assert result == {"objects": []}
    
    @pytest.mark.asyncio
    async def test_fetch_valid_ids(self):
        """Test fetch with valid IDs returns objects."""
        mock_objects = [
            {
                "id": "doc1",
                "content": "This is the full content of document 1.",
                "metadata": {
                    "title": "Document 1",
                    "source": "test_source",
                    "truncated": False
                }
            },
            {
                "id": "doc2",
                "content": "This is the full content of document 2.",
                "metadata": {
                    "title": "Document 2", 
                    "source": "test_source",
                    "truncated": False
                }
            }
        ]
        
        with patch('mcp_private_db.tools.get_pinecone_client') as mock_client:
            mock_pinecone = Mock()
            mock_pinecone.fetch.return_value = mock_objects
            mock_client.return_value = mock_pinecone
            
            result = await fetch(["doc1", "doc2"])
            
            assert result == {"objects": mock_objects}
            mock_pinecone.fetch.assert_called_once_with(["doc1", "doc2"])
    
    @pytest.mark.asyncio
    async def test_fetch_too_many_ids(self):
        """Test fetch with too many IDs returns empty results."""
        too_many_ids = [f"doc{i}" for i in range(51)]  # 51 IDs
        
        result = await fetch(too_many_ids)
        assert result == {"objects": []}
    
    @pytest.mark.asyncio
    async def test_fetch_invalid_ids(self):
        """Test fetch with invalid IDs (empty strings, None) filters them out."""
        mock_objects = [{"id": "doc1", "content": "content", "metadata": {}}]
        
        with patch('mcp_private_db.tools.get_pinecone_client') as mock_client:
            mock_pinecone = Mock()
            mock_pinecone.fetch.return_value = mock_objects
            mock_client.return_value = mock_pinecone
            
            result = await fetch(["doc1", "", "   ", None])
            
            # Should only fetch the valid ID
            mock_pinecone.fetch.assert_called_once_with(["doc1"])
    
    @pytest.mark.asyncio
    async def test_fetch_pinecone_error(self):
        """Test fetch handles Pinecone errors gracefully."""
        with patch('mcp_private_db.tools.get_pinecone_client') as mock_client:
            mock_client.side_effect = Exception("Pinecone error")
            
            result = await fetch(["doc1"])
            assert result == {"objects": []}


class TestMCPRegistration:
    """Test that MCP tools are properly registered."""
    
    def test_mcp_tools_registered(self):
        """Test that exactly two tools are available via API."""
        from mcp_private_db.main import app
        
        # Test that the app has the correct endpoints
        routes = [route.path for route in app.routes]
        
        # Should have the tool endpoints
        assert "/tools/search" in routes
        assert "/tools/fetch" in routes
        assert "/tools" in routes
        assert "/call" in routes
