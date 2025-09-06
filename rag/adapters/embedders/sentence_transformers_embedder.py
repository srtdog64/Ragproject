# adapters/embedders/sentence_transformers_embedder.py
from __future__ import annotations
from typing import List, Sequence, Optional
import threading
import logging
from .base import IEmbedder, Result, l2norm

logger = logging.getLogger(__name__)

class SentenceTransformersEmbedder(IEmbedder):
    def __init__(self, model: str, dim: int = 384, normalize: bool = True,
                 device: Optional[str] = None, batchSize: int = 64, name: Optional[str] = None):
        self._modelName = model
        self._normalize = bool(normalize)
        self._device = device
        self._batch = max(1, int(batchSize))
        self._dim = int(dim)
        self._name = name or f"st::{model}"
        self._model = None
        self._lock = threading.Lock()
        
        # Add properties for namespace compatibility
        self.model_name = model
        self.dimension = dim

    def getDim(self) -> int:
        if self._model is None:
            self._ensureLoaded()
        return self._dim

    def getName(self) -> str:
        return self._name

    def embedText(self, text: str) -> List[float]:
        return self.embedTexts([text or ""])[0]

    def embedTexts(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        self._ensureLoaded()
        if self._model == "fallback":
            from .base import FallbackEmbedder
            return FallbackEmbedder(dim=self._dim, normalize=self._normalize, name="st_fallback").embedTexts(texts)
        return self._encode(texts)

    def _ensureLoaded(self) -> Result[None]:
        if self._model is not None:
            return Result.Ok(None)
        
        with self._lock:
            if self._model is not None:
                return Result.Ok(None)
            try:
                from sentence_transformers import SentenceTransformer
                kwargs = {}
                if self._device and self._device != "auto":
                    kwargs["device"] = self._device
                
                logger.info(f"Loading model: {self._modelName}")
                self._model = SentenceTransformer(self._modelName, **kwargs)
                self._dim = int(self._model.get_sentence_embedding_dimension())
                logger.info(f"Model loaded successfully: {self._modelName} (dim={self._dim})")
                return Result.Ok(None)
                
            except Exception as e:
                logger.error(f"Failed to load model {self._modelName}: {e}")
                self._model = "fallback"
                return Result.Err(f"fallback: {type(e).__name__}: {e}")

    def _encode(self, texts: Sequence[str]) -> List[List[float]]:
        try:
            # Try with normalize_embeddings parameter first
            embs = self._model.encode(
                list(texts),
                batch_size=self._batch,
                convert_to_numpy=True,
                show_progress_bar=False,
                normalize_embeddings=self._normalize
            )
        except TypeError:
            # Fallback for older versions without normalize_embeddings
            arr = self._model.encode(
                list(texts),
                batch_size=self._batch,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            if self._normalize:
                import numpy as np
                norms = np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12
                arr = arr / norms
            embs = arr
        
        return [row.astype("float32").tolist() for row in embs]
