# chunkers/utils/metadata_helper.py
"""
Helper utilities for managing chunk metadata
"""
from typing import Dict, Any, Optional
import hashlib
from datetime import datetime


def create_chunk_meta(
    doc, 
    chunk_type: str = "default",
    chunk_index: Optional[int] = None,
    **extra_meta
) -> Dict[str, Any]:
    """
    Create standard metadata for a chunk
    
    Args:
        doc: Document object with title and source attributes
        chunk_type: Type of chunking strategy used
        chunk_index: Index of this chunk within the document
        **extra_meta: Additional metadata to include
    
    Returns:
        Dictionary of metadata with standard fields
    """
    meta = {
        "docTitle": doc.title,
        "docSource": doc.source,
        "chunkType": chunk_type,
        "timestamp": datetime.now().isoformat()
    }
    
    if chunk_index is not None:
        meta["chunkIndex"] = chunk_index
    
    # Add any extra metadata provided
    meta.update(extra_meta)
    
    return meta


def generate_chunk_id(doc_id: str, chunk_index: int, chunk_type: str = None) -> str:
    """
    Generate a unique chunk ID
    
    Args:
        doc_id: Document ID
        chunk_index: Index of the chunk
        chunk_type: Optional chunk type identifier
    
    Returns:
        Unique chunk ID string
    """
    if chunk_type:
        return f"{doc_id}:{chunk_type}_{chunk_index}"
    return f"{doc_id}:chunk_{chunk_index}"


def calculate_chunk_hash(text: str) -> str:
    """
    Calculate a hash for chunk content (useful for deduplication)
    
    Args:
        text: Chunk text content
    
    Returns:
        MD5 hash of the text (first 12 characters)
    """
    return hashlib.md5(text.encode()).hexdigest()[:12]
