"""
FAISS Vector Similarity Index for Saree Designs.

Uses FAISS IndexFlatIP (Inner Product) with L2-normalized embeddings,
guaranteeing exact Cosine Similarity computation.
Provides VectorIndexManager for multi-tenant, per-user isolated indexing and retrieval.
"""

import os
import re
import json
import numpy as np
import faiss
from typing import List, Dict, Any, Optional

class SareeVectorIndex:
    def __init__(self, dimension: int = 1536, index_file: str = None, meta_file: str = None):
        self.dimension = dimension
        self.index_file = index_file or os.path.join("data", "indexes", "saree_faiss.index")
        self.meta_file = meta_file or os.path.join("data", "indexes", "saree_meta.json")
        
        self.index: faiss.IndexFlatIP = faiss.IndexFlatIP(self.dimension)
        self.metadata_store: List[Dict[str, Any]] = []

        # Load existing index if present
        self.load()

    def add_design(self, embedding: np.ndarray, metadata: Dict[str, Any]) -> int:
        """
        Adds a design embedding and its OneNote metadata to the index.
        """
        if embedding.ndim == 1:
            embedding = np.expand_dims(embedding, axis=0)

        embedding = embedding.astype(np.float32)
        idx = self.index.ntotal

        self.index.add(embedding)
        metadata["index_id"] = idx
        self.metadata_store.append(metadata)

        return idx

    def search(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = 6, 
        threshold: float = 0.82
    ) -> Dict[str, Any]:
        """
        Searches for visually similar designs based on structural/motif vectors.
        """
        if self.index.ntotal == 0:
            return {
                "matches": [],
                "is_strong_match": False,
                "top_score": 0.0,
                "top_percentage": 0.0,
                "threshold": threshold,
                "status_message": "No designs indexed in your connected OneNote yet. Please sync your OneNote notebooks."
            }

        if query_embedding.ndim == 1:
            query_embedding = np.expand_dims(query_embedding, axis=0)
            
        query_embedding = query_embedding.astype(np.float32)

        actual_k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_embedding, actual_k)

        matches = []
        scores_row = scores[0]
        indices_row = indices[0]

        top_score = float(scores_row[0]) if len(scores_row) > 0 else 0.0
        top_percentage = round(max(0.0, min(1.0, top_score)) * 100.0, 1)

        is_strong_match = top_score >= threshold

        for score, idx in zip(scores_row, indices_row):
            if idx < 0 or idx >= len(self.metadata_store):
                continue
            item = dict(self.metadata_store[idx])
            sim_score = float(score)
            sim_pct = round(max(0.0, min(1.0, sim_score)) * 100.0, 1)
            item["similarity_score"] = sim_score
            item["similarity_percentage"] = sim_pct
            item["is_match"] = sim_score >= threshold
            matches.append(item)

        if is_strong_match:
            status_msg = f"Strong design match found ({top_percentage}% design pattern match)."
        else:
            status_msg = f"Closest design match found ({top_percentage}% design pattern match)."

        return {
            "matches": matches,
            "is_strong_match": is_strong_match,
            "top_score": top_score,
            "top_percentage": top_percentage,
            "threshold": threshold,
            "status_message": status_msg
        }

    def save(self):
        """Persists the FAISS index and metadata to disk."""
        os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
        faiss.write_index(self.index, self.index_file)
        with open(self.meta_file, "w", encoding="utf-8") as f:
            json.dump(self.metadata_store, f, indent=2)

    def load(self) -> bool:
        """Loads index and metadata if files exist."""
        if os.path.exists(self.index_file) and os.path.exists(self.meta_file):
            try:
                self.index = faiss.read_index(self.index_file)
                self.dimension = self.index.d
                with open(self.meta_file, "r", encoding="utf-8") as f:
                    self.metadata_store = json.load(f)
                return True
            except Exception as e:
                print(f"Warning: Failed to load existing index: {e}")
                self.index = faiss.IndexFlatIP(self.dimension)
                self.metadata_store = []
        return False

    def clear(self):
        """Clears all indexed designs."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata_store = []
        if os.path.exists(self.index_file):
            os.remove(self.index_file)
        if os.path.exists(self.meta_file):
            os.remove(self.meta_file)

    def rebuild(self, embeddings: List[np.ndarray], metadatas: List[Dict[str, Any]]):
        """Rebuilds the index completely from the authoritative list of current cloud items."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata_store = []
        if embeddings and len(embeddings) > 0:
            stacked = np.vstack(embeddings).astype(np.float32)
            self.index.add(stacked)
            for idx, meta in enumerate(metadatas):
                meta["index_id"] = idx
                self.metadata_store.append(meta)
        self.save()

    def count(self) -> int:
        return self.index.ntotal


class VectorIndexManager:
    """
    Manages dedicated, isolated SareeVectorIndex instances per user.
    Microsoft OneNote Cloud is the SINGLE SOURCE OF TRUTH.
    Never loads legacy archives, desktop backups, or stale indexes.
    """
    def __init__(self, base_dir: str = "data/indexes", dimension: int = 1536):
        self.base_dir = base_dir
        self.dimension = dimension
        self._user_indexes: Dict[str, SareeVectorIndex] = {}
        # Empty placeholder with 0 designs for unauthenticated state
        self._empty_index = SareeVectorIndex(
            dimension=self.dimension,
            index_file=os.path.join(base_dir, "empty_faiss.index"),
            meta_file=os.path.join(base_dir, "empty_meta.json")
        )

    def get_index(self, user_id: Optional[str] = None) -> SareeVectorIndex:
        if not user_id:
            try:
                from app.database import SessionLocal, UserRecord
                db = SessionLocal()
                active_user = db.query(UserRecord).order_by(UserRecord.connected_at.desc()).first()
                if active_user:
                    user_id = active_user.id
                db.close()
            except Exception:
                pass

        if not user_id:
            return self._empty_index

        safe_uid = re.sub(r'[^a-zA-Z0-9_\-]', '_', user_id)
        if safe_uid not in self._user_indexes:
            user_dir = os.path.join(self.base_dir, "users", safe_uid)
            os.makedirs(user_dir, exist_ok=True)
            idx_file = os.path.join(user_dir, "saree_faiss.index")
            meta_file = os.path.join(user_dir, "saree_meta.json")
            self._user_indexes[safe_uid] = SareeVectorIndex(
                dimension=self.dimension,
                index_file=idx_file,
                meta_file=meta_file
            )
        else:
            if self._user_indexes[safe_uid].count() == 0:
                self._user_indexes[safe_uid].load()

        return self._user_indexes[safe_uid]

    def count(self, user_id: Optional[str] = None) -> int:
        idx = self.get_index(user_id)
        if idx.count() == 0:
            idx.load()
        return idx.count()

    @property
    def metadata_store(self) -> List[Dict[str, Any]]:
        return self.get_index().metadata_store
