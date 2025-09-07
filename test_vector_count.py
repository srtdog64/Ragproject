#!/usr/bin/env python
"""
Test vector count directly from ChromaDB
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rag'))

def test_vector_count():
    """Test direct access to ChromaDB to get vector count"""
    import chromadb
    from chromadb.config import Settings
    
    # Use the path from config
    persist_dir = r"E:\Ragproject\chroma_db"
    
    print(f"Checking ChromaDB at: {persist_dir}")
    print("-" * 60)
    
    try:
        # Create client
        client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # List all collections
        collections = client.list_collections()
        print(f"Found {len(collections)} collections:")
        
        total_vectors = 0
        for collection in collections:
            count = collection.count()
            total_vectors += count
            print(f"  - {collection.name}: {count} vectors")
            
            # Get metadata if available
            try:
                metadata = collection.metadata
                if metadata:
                    print(f"    Metadata: {metadata}")
            except:
                pass
        
        print("-" * 60)
        print(f"Total vectors across all collections: {total_vectors}")
        
        return total_vectors
        
    except Exception as e:
        print(f"Error accessing ChromaDB: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    count = test_vector_count()
    print(f"\nFinal count: {count}")
