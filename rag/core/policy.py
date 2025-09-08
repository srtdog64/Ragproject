# core/policy.py
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Policy:
    """Simple policy for RAG pipeline configuration"""
    maxContextChars: int = 12000
    retrieveK: int = 20  # How many to retrieve from vector store
    rerankK: int = 5     # How many to keep after reranking

    def getMaxContextChars(self) -> int:
        return self.maxContextChars

    def setMaxContextChars(self, n: int) -> None:
        self.maxContextChars = max(2000, n)

    def getRetrieveK(self) -> int:
        """Get number of documents to retrieve from vector store"""
        return self.retrieveK

    def setRetrieveK(self, k: int) -> None:
        self.retrieveK = max(1, k)
    
    def getRerankK(self) -> int:
        """Get number of documents to keep after reranking"""
        return self.rerankK
    
    def setRerankK(self, k: int) -> None:
        self.rerankK = max(1, min(k, self.retrieveK))  # Can't be more than retrieveK
    
    # For backward compatibility
    def getDefaultTopK(self) -> int:
        """Deprecated: Use getRetrieveK() instead"""
        return self.retrieveK
