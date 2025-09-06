# stores/chroma_store.py
"""
ChromaDB-based persistent vector store implementation
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
import logging
import chromadb
from chromadb.config import Settings
from core.types import Chunk, Retrieved
from core.interfaces import VectorStore

logger = logging.getLogger(__name__)

class ChromaVectorStore(VectorStore):
    """
    Persistent vector store using ChromaDB
    """
    
    def __init__(self, 
                 persist_directory: str = "./chroma_db",
                 collection_name: str = "rag_documents"):
        """
        Initialize ChromaDB client and collection
        
        Args:
            persist_directory: Directory to persist the database
            collection_name: Name of the collection to use
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            # Get current count
            count = self.collection.count()
            logger.info(f"ChromaDB: Loaded existing collection '{collection_name}' with {count} documents")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
            logger.info(f"ChromaDB: Created new collection '{collection_name}'")
    
    def addMany(self, chunks: List[Chunk], vectors: List[List[float]]) -> None:
        """
        Add multiple chunks with their embeddings to the store
        """
        if not chunks:
            return
        
        # Prepare data for ChromaDB
        ids = [chunk.id for chunk in chunks]
        embeddings = vectors
        metadatas = []
        documents = []
        
        for chunk in chunks:
            # Combine chunk metadata
            metadata = {
                "docId": chunk.docId,
                "docTitle": chunk.docTitle,
                "docSource": chunk.docSource,
                "chunkIndex": chunk.meta.get("chunkIndex", 0)
            }
            # Add any additional metadata from chunk.meta
            for key, value in chunk.meta.items():
                if key not in metadata:
                    # ChromaDB requires metadata values to be strings, ints, floats, or bools
                    if isinstance(value, (str, int, float, bool)):
                        metadata[key] = value
            
            metadatas.append(metadata)
            documents.append(chunk.text)
        
        # Add to ChromaDB
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        
        logger.info(f"ChromaDB: Added {len(chunks)} chunks (total now: {self.collection.count()})")
    
    def upsert(self, chunk: Chunk, vector: List[float]) -> None:
        """
        Update or insert a single chunk
        """
        metadata = {
            "docId": chunk.docId,
            "docTitle": chunk.docTitle,
            "docSource": chunk.docSource,
            "chunkIndex": chunk.meta.get("chunkIndex", 0)
        }
        
        # Add to collection (ChromaDB handles upsert automatically)
        self.collection.upsert(
            ids=[chunk.id],
            embeddings=[vector],
            metadatas=[metadata],
            documents=[chunk.text]
        )
        
        logger.debug(f"ChromaDB: Upserted chunk {chunk.id}")
    
    def deleteByDoc(self, docId: str) -> None:
        """
        Delete all chunks belonging to a specific document
        """
        # Query for all chunks with this docId
        results = self.collection.get(
            where={"docId": docId}
        )
        
        if results['ids']:
            self.collection.delete(ids=results['ids'])
            logger.info(f"ChromaDB: Deleted {len(results['ids'])} chunks for doc {docId}")
    
    def search(self, queryVector: List[float], k: int, 
              metaFilter: Optional[Dict[str, Any]] = None) -> List[Retrieved]:
        """
        Search for similar chunks using the query vector
        """
        logger.info(f"ChromaDB: Searching with k={k}, filter={metaFilter}")
        
        # Prepare ChromaDB where clause from metaFilter
        where_clause = None
        if metaFilter:
            where_clause = metaFilter
        
        # Query the collection
        results = self.collection.query(
            query_embeddings=[queryVector],
            n_results=min(k, self.collection.count() or 1),  # Ensure we don't request more than exists
            where=where_clause
        )
        
        # Convert results to Retrieved objects
        retrieved = []
        if results['ids'] and results['ids'][0]:  # ChromaDB returns nested lists
            for i in range(len(results['ids'][0])):
                # Reconstruct chunk from stored data
                chunk = Chunk(
                    id=results['ids'][0][i],
                    docId=results['metadatas'][0][i]['docId'],
                    docTitle=results['metadatas'][0][i]['docTitle'],
                    docSource=results['metadatas'][0][i]['docSource'],
                    text=results['documents'][0][i],
                    meta={
                        k: v for k, v in results['metadatas'][0][i].items()
                        if k not in ['docId', 'docTitle', 'docSource']
                    }
                )
                
                # ChromaDB returns distances, convert to similarity score (1 - distance for cosine)
                score = 1.0 - results['distances'][0][i]
                
                retrieved.append(Retrieved(chunk=chunk, score=score))
        
        logger.info(f"ChromaDB: Found {len(retrieved)} results")
        return retrieved
    
    def clear(self) -> None:
        """
        Clear all documents from the collection
        """
        # Delete and recreate the collection
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"ChromaDB: Cleared collection '{self.collection_name}'")
    
    def count(self) -> int:
        """
        Get the total number of documents in the collection
        """
        return self.collection.count()
