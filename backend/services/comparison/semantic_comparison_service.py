"""Service for generating embeddings and performing semantic comparison of obligations."""

from __future__ import annotations

import logging
import uuid
import math
import hashlib
from sqlalchemy import select
from sqlalchemy.orm import Session
from google import genai

from backend.config.settings import Settings, get_settings
from backend.models.clause import Clause
from backend.models.obligation import Obligation

logger = logging.getLogger(__name__)


def _generate_mock_vector(text: str, dimensions: int = 768) -> list[float]:
    """Generates a deterministic normalized mock vector for offline testing."""
    import random
    hasher = hashlib.sha256(text.encode("utf-8"))
    seed_int = int.from_bytes(hasher.digest()[:8], byteorder="big")
    rng = random.Random(seed_int)
    
    vector = [rng.gauss(0, 1) for _ in range(dimensions)]
    square_sum = sum(v * v for v in vector)
    norm = math.sqrt(square_sum)
    if norm > 0:
        vector = [v / norm for v in vector]
    return vector


def compute_cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Computes cosine similarity between two float vectors, bounding the result in [0, 1]."""
    if len(vec_a) != len(vec_b) or not vec_a or not vec_b:
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    score = dot_product / (norm_a * norm_b)
    return max(0.0, min(1.0, score))


from backend.services.ai.gemini_client import create_gemini_client

class SemanticComparisonService:
    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self._db = db
        self._settings = settings or get_settings()
        self._client = create_gemini_client(self._settings)

    def get_embedding(self, text: str) -> list[float]:
        """Generates text embedding using Gemini or mock fallback."""
        if not text.strip():
            return [0.0] * 768

        if self._client is None:
            return _generate_mock_vector(text)

        try:
            response = self._client.models.embed_content(
                model="text-embedding-004",
                contents=text
            )
            if response.embeddings and response.embeddings[0].values:
                return response.embeddings[0].values
            raise ValueError("No embedding values returned from Gemini API.")
        except Exception as exc:
            logger.error("Gemini embedding generation failed: %s. Falling back to mock.", exc)
            return _generate_mock_vector(text)

    def get_obligation_text_representation(self, ob: Obligation) -> str:
        """Constructs a unified text representation of an obligation for embedding."""
        parts = [
            f"Subject: {ob.subject}",
            f"Modality: {ob.modality}",
            f"Action: {ob.action}",
            f"Object: {ob.object}",
        ]
        if ob.conditions:
            parts.append(f"Conditions: {ob.conditions}")
        if ob.time_constraint:
            parts.append(f"Time constraint: {ob.time_constraint}")
        return " | ".join(parts)

    def compare_obligations(self, ob_a: Obligation, ob_b: Obligation) -> tuple[float, str]:
        """Compares two obligations, returns similarity score and category."""
        text_a = self.get_obligation_text_representation(ob_a)
        text_b = self.get_obligation_text_representation(ob_b)

        # Exact matching representation shortcut
        if text_a == text_b:
            return 1.0, "Exact Match"

        vec_a = self.get_embedding(text_a)
        vec_b = self.get_embedding(text_b)
        score = compute_cosine_similarity(vec_a, vec_b)

        if score >= 0.98:
            category = "Exact Match"
        elif score >= 0.70:
            category = "Similar"
        else:
            category = "Different"

        return score, category

    def compare_versions(
        self, version_a_id: uuid.UUID, version_b_id: uuid.UUID
    ) -> list[dict]:
        """Performs pairwise semantic comparison of obligations in two policy versions."""
        obs_a = self._db.scalars(
            select(Obligation)
            .join(Clause, Clause.id == Obligation.clause_id)
            .where(
                Clause.policy_version_id == version_a_id,
                Obligation.deleted_at.is_(None)
            )
        ).all()

        obs_b = self._db.scalars(
            select(Obligation)
            .join(Clause, Clause.id == Obligation.clause_id)
            .where(
                Clause.policy_version_id == version_b_id,
                Obligation.deleted_at.is_(None)
            )
        ).all()

        results = []
        for ob_a in obs_a:
            for ob_b in obs_b:
                score, category = self.compare_obligations(ob_a, ob_b)
                results.append({
                    "obligation_a": ob_a,
                    "obligation_b": ob_b,
                    "similarity_score": score,
                    "category": category
                })

        return results
