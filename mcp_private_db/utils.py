"""Utility functions for text processing and content management."""

import re
from typing import Optional, Dict, Any


def clean_text(text: str) -> str:
    """Clean text by removing control characters and ensuring UTF-8 encoding."""
    if not text:
        return ""
    
    # Remove control characters except newlines and tabs
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Ensure UTF-8 encoding
    try:
        cleaned.encode('utf-8')
    except UnicodeEncodeError:
        # Replace problematic characters
        cleaned = cleaned.encode('utf-8', errors='replace').decode('utf-8')
    
    return cleaned.strip()


def truncate_content(content: str, max_chars: int) -> tuple[str, bool]:
    """Truncate content to max_chars and return (truncated_content, was_truncated)."""
    if not content:
        return "", False
    
    if len(content) <= max_chars:
        return content, False
    
    # Truncate at word boundary if possible
    truncated = content[:max_chars]
    last_space = truncated.rfind(' ')
    
    if last_space > max_chars * 0.8:  # Only use word boundary if it's not too far back
        truncated = truncated[:last_space]
    
    return truncated, True


def extract_text_from_metadata(metadata: Dict[str, Any], text_keys: list[str]) -> Optional[str]:
    """Extract text content from metadata using the specified keys in order."""
    for key in text_keys:
        if key in metadata and metadata[key]:
            text = str(metadata[key]).strip()
            if text:
                return text
    return None


def create_snippet(text: str, max_length: int = 200) -> str:
    """Create a snippet from text, truncated to max_length."""
    if not text:
        return ""
    
    text = clean_text(text)
    if len(text) <= max_length:
        return text
    
    # Truncate at word boundary
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:
        truncated = truncated[:last_space]
    
    return truncated + "..."
