# stores/chroma_store.py
"""
ChromaDB-based persistent vector store implementation with namespace support
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
import logging
import chromadb
from chromadb.config import Settings
from core.types import Chunk, Retrieved
from core.interfaces import VectorStore
from stores.namespace_manager import NamespaceManager

logger = logging.getLogger(__name__)

class ChromaVectorStore(VectorStore):
    """
    Persistent vector store using ChromaDB
    """
    
    def __init__(self, 
                 persist_directory: str = "./chroma_db",
                 collection_name: str = "rag_documents",
                 embedding_model: str = None,
                 embedding_dim: int = None):
        """
        Initialize ChromaDB client and collection with namespace support
        
        Args:
            persist_directory: Directory to persist the database
            collection_name: Base name of the collection
            embedding_model: Name of the embedding model (for namespace)
            embedding_dim: Dimension of embeddings (for namespace)
        """
        self.persist_directory = persist_directory
        self.base_collection_name = collection_name
        self.embedding_model = embedding_model
        self.embedding_dim = embedding_dim
        self._closed = False
        
        # Initialize namespace manager
        self.namespace_manager = NamespaceManager(collection_name)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Determine collection name based on embedding model
        if embedding_model:
            self.collection_name = self.namespace_manager.get_namespace_for_model(
                embedding_model, embedding_dim
            )
        else:
            self.collection_name = collection_name
            logger.warning("No embedding model specified, using base collection name")
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            # Get current count
            count = self.collection.count()
            logger.info(f"ChromaDB: Loaded existing collection '{self.collection_name}' with {count} documents")
            logger.info(f"  Model: {embedding_model}")
            logger.info(f"  Dimensions: {embedding_dim}")
        except:
            # Create collection with metadata
            metadata = self.namespace_manager.create_namespace_metadata(
                embedding_model or "default",
                embedding_dim or 384
            )
            metadata["hnsw:space"] = "cosine"  # Add HNSW config
            
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata=metadata
            )
            logger.info(f"ChromaDB: Created new collection '{self.collection_name}'")
            logger.info(f"  Model: {embedding_model}")
            logger.info(f"  Dimensions: {embedding_dim}")
    
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
            # Start with chunk's metadata
            metadata = dict(chunk.meta) if chunk.meta else {}
            # Add docId as it's a separate field in Chunk
            metadata["docId"] = chunk.docId
            
            # Ensure all values are ChromaDB compatible types
            clean_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    clean_metadata[key] = value
                elif value is None:
                    clean_metadata[key] = ""  # Convert None to empty string
                else:
                    clean_metadata[key] = str(value)  # Convert other types to string
            
            metadatas.append(clean_metadata)
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
        # Start with chunk's metadata
        metadata = dict(chunk.meta) if chunk.meta else {}
        # Add docId
        metadata["docId"] = chunk.docId
        
        # Clean metadata for ChromaDB
        clean_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                clean_metadata[key] = value
            elif value is None:
                clean_metadata[key] = ""
            else:
                clean_metadata[key] = str(value)
        
        # Add to collection (ChromaDB handles upsert automatically)
        self.collection.upsert(
            ids=[chunk.id],
            embeddings=[vector],
            metadatas=[clean_metadata],
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
                metadata = results['metadatas'][0][i]
                chunk = Chunk(
                    id=results['ids'][0][i],
                    docId=metadata.get('docId', ''),
                    text=results['documents'][0][i],
                    meta={k: v for k, v in metadata.items() if k != 'docId'}
                )
                
                # ChromaDB returns distances, convert to similarity score (1 - distance for cosine)
                score = 1.0 - results['distances'][0][i]
                
                retrieved.append(Retrieved(chunk=chunk, score=score))
        
        logger.info(f"ChromaDB: Found {len(retrieved)} results")
        return retrieved
    
    def close(self) -> None:
        """Release underlying Chroma resources"""
        if self._closed:
            return
        self._closed = True
        try:
            system = getattr(self.client, "_system", None)
            if system and getattr(system, "_running", False):
                system.stop()
                logger.info("ChromaDB: Client system stopped")
        except Exception as e:
            logger.warning(f"ChromaDB: Failed to stop client system: {e}")
        finally:
            self.client = None
            self.collection = None
    
    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
    
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
    
    def list_namespaces(self) -> List[Dict[str, Any]]:
        """
        List all available namespaces (collections) with their model info
        
        Returns:
            List of namespace information
        """
        return self.namespace_manager.list_available_namespaces(self.client)
    
    def switch_namespace(self, embedding_model: str, embedding_dim: int = None) -> bool:
        """
        Switch to a different namespace (for different embedding model)
        
        Args:
            embedding_model: Name of the embedding model
            embedding_dim: Dimension of embeddings
            
        Returns:
            True if successful
        """
        try:
            # Generate namespace for the model
            new_namespace = self.namespace_manager.get_namespace_for_model(
                embedding_model, embedding_dim
            )
            
            # Try to get existing collection
            try:
                self.collection = self.client.get_collection(name=new_namespace)
                count = self.collection.count()
                logger.info(f"Switched to existing namespace: {new_namespace} ({count} documents)")
            except:
                # Create new collection for this model
                metadata = self.namespace_manager.create_namespace_metadata(
                    embedding_model, embedding_dim or 384
                )
                metadata["hnsw:space"] = "cosine"
                
                self.collection = self.client.create_collection(
                    name=new_namespace,
                    metadata=metadata
                )
                logger.info(f"Created new namespace: {new_namespace}")
            
            # Update current settings
            self.collection_name = new_namespace
            self.embedding_model = embedding_model
            self.embedding_dim = embedding_dim
            self.namespace_manager.switch_namespace(new_namespace)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch namespace: {e}")
            return False
