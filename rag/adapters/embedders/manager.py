# adapters/embedders/manager.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Sequence, List
import json, hashlib, threading
import logging
import yaml  # pip install pyyaml

from .base import IEmbedder, Result, koRatio
from .base import FallbackEmbedder
from .sentence_transformers_embedder import SentenceTransformersEmbedder

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class EmbedderProfile:
    kind: str
    model: Optional[str] = None
    dim: int = 384
    normalize: bool = True
    device: Optional[str] = None
    batchSize: int = 64
    name: Optional[str] = None

class EmbedderPolicy:
    def __init__(self, cfg: dict):
        self._koThreshold = float(cfg.get("koThreshold", 0.30))
        self._preferGpu = bool(cfg.get("preferGpu", True))
        self._costTier = str(cfg.get("costTier", "free"))
        self._order = list(cfg.get("order", []))

    def decide(self, registry: Dict[str, EmbedderProfile], texts: Sequence[str]) -> str:
        """Decide which embedder to use based on text characteristics"""
        ratio = koRatio(texts)
        
        # If Korean text ratio is high, prefer multilingual models
        if ratio > self._koThreshold:
            if "multilingual_minilm" in registry:
                return "multilingual_minilm"
            if "multilingual_base" in registry:
                return "multilingual_base"
            if "korean_roberta" in registry:
                return "korean_roberta"
        
        # Follow the order preference
        for name in self._order:
            if name in registry:
                return name
        
        # Last resort
        return next(iter(registry.keys()), "fallback_384")

class EmbedderManager:
    def __init__(self, defaultKey: str, profiles: Dict[str, EmbedderProfile], policy: EmbedderPolicy):
        self._defaultKey = defaultKey
        self._profiles = profiles
        self._policy = policy
        self._cache: Dict[str, IEmbedder] = {}
        self._lock = threading.Lock()

    @staticmethod
    def fromYaml(path: str) -> "EmbedderManager":
        try:
            with open(path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load embeddings config from {path}: {e}")
            logger.info("Using fallback configuration")
            # Minimal fallback configuration
            fallback = {"fallback_384": EmbedderProfile(kind="deterministic-fallback", dim=384, normalize=True)}
            return EmbedderManager("fallback_384", fallback, EmbedderPolicy({}))
        
        emb = cfg.get("embedders", {})
        defaultKey = str(emb.get("default", "auto"))
        reg = emb.get("registry", {}) or {}
        
        profiles: Dict[str, EmbedderProfile] = {}
        for key, val in reg.items():
            profiles[key] = EmbedderProfile(
                kind=str(val.get("kind", "")),
                model=val.get("model"),
                dim=int(val.get("dim", 384)),
                normalize=bool(val.get("normalize", True)),
                device=val.get("device"),
                batchSize=int(val.get("batchSize", 64)),
                name=key
            )
        
        policy = EmbedderPolicy(cfg.get("policy", {}))
        logger.info(f"Loaded {len(profiles)} embedder profiles from {path}")
        return EmbedderManager(defaultKey, profiles, policy)

    def resolve(self, profileName: Optional[str], textsForPolicy: Sequence[str]) -> Tuple[IEmbedder, str]:
        """Resolve embedder and return (embedder, signature)"""
        key = self._selectKey(profileName, textsForPolicy)
        return self._getOrCreate(key), self._signatureFor(key)

    def namespaceFor(self, signature: str) -> str:
        """Generate namespace from signature"""
        return f"emb::{signature}"

    def ensureDim(self, expected: int, embedder: IEmbedder) -> Result[None]:
        """Ensure embedder dimension matches expected"""
        if expected <= 0:
            return Result.Err("expected dim invalid")
        if embedder.getDim() != expected:
            return Result.Err(f"dim mismatch: index={expected} embedder={embedder.getDim()}")
        return Result.Ok(None)

    def getDefaultEmbedder(self) -> IEmbedder:
        """Get default embedder based on config"""
        return self.resolve(self._defaultKey, [])[0]

    # ---------- internal
    def _selectKey(self, profileName: Optional[str], texts: Sequence[str]) -> str:
        if profileName and profileName != "auto":
            return profileName
        if self._defaultKey and self._defaultKey != "auto":
            return self._defaultKey
        return self._policy.decide(self._profiles, texts)

    def _getOrCreate(self, key: str) -> IEmbedder:
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            emb = self._construct(key)
            self._cache[key] = emb
            return emb

    def _construct(self, key: str) -> IEmbedder:
        prof = self._profiles.get(key)
        if prof is None:
            logger.warning(f"Profile '{key}' not found, using fallback")
            return FallbackEmbedder(dim=384, normalize=True, name="fallback_384")
        
        if prof.kind == "sentence-transformers":
            return SentenceTransformersEmbedder(
                model=prof.model or "all-MiniLM-L6-v2",
                dim=prof.dim,
                normalize=prof.normalize,
                device=prof.device,
                batchSize=prof.batchSize,
                name=key
            )
        
        if prof.kind == "deterministic-fallback":
            return FallbackEmbedder(dim=prof.dim, normalize=prof.normalize, name=key)
        
        # Future extension point for other embedder types
        logger.warning(f"Unknown embedder kind: {prof.kind}, using fallback")
        return FallbackEmbedder(dim=prof.dim, normalize=prof.normalize, name=f"{key}_fb")

    def _signatureFor(self, key: str) -> str:
        """Generate signature for embedder configuration"""
        prof = self._profiles.get(key)
        if prof is None:
            raw = {"kind": "fallback", "dim": 384, "normalize": True}
        else:
            raw = {"kind": prof.kind, "model": prof.model, "dim": prof.dim,
                   "normalize": prof.normalize, "device": prof.device, "batchSize": prof.batchSize}
        blob = json.dumps(raw, sort_keys=True)
        h = hashlib.sha256(blob.encode()).hexdigest()[:12]
        return f"{key}:{h}"
