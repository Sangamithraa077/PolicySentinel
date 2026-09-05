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
    """Generates a deterministic, normalized semantic vector using token hashing and n-grams
    so semantically related texts have high cosine similarity while unrelated texts have low similarity."""
    import re
    tokens = re.findall(r'[a-zA-Z0-9]+', text.lower())
    if not tokens:
        return [0.0] * dimensions

    vector = [0.0] * dimensions
    # Common function words to de-weight
    stop_words = {"the", "a", "an", "and", "or", "to", "in", "of", "for", "with", "on", "at", "by", "from", "is", "are", "be", "subject", "action", "object", "modality", "conditions", "time", "constraint"}

    for token in tokens:
        weight = 0.2 if token in stop_words else 1.0
        h = int(hashlib.md5(token.encode("utf-8")).hexdigest()[:8], 16)
        vector[h % dimensions] += weight

    # Bigrams to capture compound concepts (e.g. incident response, data retention, access control)
    for i in range(len(tokens) - 1):
        bigram = f"{tokens[i]}_{tokens[i+1]}"
        h = int(hashlib.md5(bigram.encode("utf-8")).hexdigest()[:8], 16)
        vector[h % dimensions] += 1.5

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
    _api_failed = False

    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self._db = db
        self._settings = settings or get_settings()
        self._client = create_gemini_client(self._settings)

    def get_embedding(self, text: str) -> list[float]:
        """Generates text embedding using Gemini or fast local semantic vector."""
        if not text.strip():
            return [0.0] * 768

        if self._client is None or SemanticComparisonService._api_failed:
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
            logger.warning("Gemini embedding generation failed (%s). Caching failure and using local semantic vector.", exc)
            SemanticComparisonService._api_failed = True
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

        if text_a == text_b:
            return 1.0, "Exact Match"

        vec_a = self.get_embedding(text_a)
        vec_b = self.get_embedding(text_b)
        score = compute_cosine_similarity(vec_a, vec_b)

        if score >= 0.98:
            category = "Exact Match"
        elif score >= 0.60:
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

        # Precompute embeddings once per obligation to avoid NxM redundant calls
        vecs_a = {ob.id: self.get_embedding(self.get_obligation_text_representation(ob)) for ob in obs_a}
        vecs_b = {ob.id: self.get_embedding(self.get_obligation_text_representation(ob)) for ob in obs_b}

        results = []
        for ob_a in obs_a:
            v_a = vecs_a[ob_a.id]
            for ob_b in obs_b:
                v_b = vecs_b[ob_b.id]
                score = compute_cosine_similarity(v_a, v_b)
                if score >= 0.98:
                    category = "Exact Match"
                elif score >= 0.60:
                    category = "Similar"
                else:
                    category = "Different"

                results.append({
                    "obligation_a": ob_a,
                    "obligation_b": ob_b,
                    "similarity_score": score,
                    "category": category
                })

        return results
