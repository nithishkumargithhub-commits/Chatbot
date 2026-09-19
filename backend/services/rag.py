"""
services/rag.py — JeevanPath AI RAG Knowledge Base Service

Provides instant, multi-lingual semantic retrieval across the 41 central
government schemes extracted from the official Skill Development Scheme booklet.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List
import numpy as np

logger = logging.getLogger(__name__)

BACKEND_DIR     = Path(__file__).resolve().parent.parent
DATA_DIR        = BACKEND_DIR / "data"
EMBEDDINGS_PATH = DATA_DIR / "embeddings.npy"
KB_CACHE_PATH   = DATA_DIR / "knowledge_base.json"
LOCAL_MODEL_DIR = BACKEND_DIR / "models" / "indic-sentence-bert-nli"
FALLBACK_MODEL  = "l3cube-pune/indic-sentence-bert-nli"

class RAGService:
    _instance = None

    def __init__(self):
        self.records: List[Dict[str, Any]] = []
        self.embeddings: np.ndarray | None = None
        self.model = None
        self._load()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RAGService()
        return cls._instance

    def _load(self):
        try:
            if KB_CACHE_PATH.exists() and EMBEDDINGS_PATH.exists():
                with open(KB_CACHE_PATH, "r", encoding="utf-8") as f:
                    self.records = json.load(f)
                self.embeddings = np.load(EMBEDDINGS_PATH)
                logger.info(f"Loaded {len(self.records)} schemes from {KB_CACHE_PATH}")
            else:
                logger.warning(f"Knowledge base files missing at {KB_CACHE_PATH}")
        except Exception as e:
            logger.error(f"Failed loading knowledge base: {e}")

    def _get_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            model_src = str(LOCAL_MODEL_DIR) if (LOCAL_MODEL_DIR / "pytorch_model.bin").exists() else FALLBACK_MODEL
            logger.info(f"Loading embedding model for RAG from: {model_src}")
            self.model = SentenceTransformer(model_src)
        return self.model

    def query(self, text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Multi-lingual semantic search across the 41 schemes.
        Works for English, Hindi, Tamil, Telugu, and other Indic queries.
        """
        if self.embeddings is None or len(self.records) == 0:
            self._load()
            if self.embeddings is None or len(self.records) == 0:
                return []

        model = self._get_model()
        q_vec = model.encode([text], normalize_embeddings=True)[0]
        sims = np.dot(self.embeddings, q_vec)
        top_indices = np.argsort(sims)[::-1][:top_k]

        results = []
        for idx in top_indices:
            rec = self.records[idx]
            results.append({
                "scheme_name": rec.get("scheme_name", ""),
                "ministry": rec.get("ministry", ""),
                "category": rec.get("category", ""),
                "section": rec.get("section_num", ""),
                "description": rec.get("description", ""),
                "assistance": rec.get("assistance", ""),
                "eligibility": rec.get("eligibility", ""),
                "how_to_apply": rec.get("how_to_apply", ""),
                "source_url": rec.get("source_url", ""),
                "similarity_score": round(float(sims[idx]), 3),
            })
        return results
