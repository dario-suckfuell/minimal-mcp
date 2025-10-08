"""Pydantic models for request/response validation."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request model for search tool."""
    query: str = Field(..., min_length=1, description="Search query text")
    top_k: Optional[int] = Field(None, ge=1, le=25, description="Number of results to return")


class SearchResult(BaseModel):
    """Individual search result."""
    id: str = Field(..., description="Document ID")
    score: float = Field(..., description="Similarity score")
    title: Optional[str] = Field(None, description="Document title")
    snippet: Optional[str] = Field(None, description="Text preview")
    source: Optional[str] = Field(None, description="Document source")


class SearchResponse(BaseModel):
    """Response model for search tool."""
    results: List[SearchResult] = Field(default_factory=list, description="Search results")


class FetchRequest(BaseModel):
    """Request model for fetch tool."""
    object_ids: List[str] = Field(..., min_length=1, max_length=50, description="List of document IDs to fetch")


class FetchObject(BaseModel):
    """Individual fetched object."""
    id: str = Field(..., description="Document ID")
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")


class FetchResponse(BaseModel):
    """Response model for fetch tool."""
    objects: List[FetchObject] = Field(default_factory=list, description="Fetched objects")
