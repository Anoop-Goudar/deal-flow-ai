from __future__ import annotations

import hashlib
import math
import re

from config import settings

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional runtime dependency
    OpenAI = None


class EmbeddingService:
    def __init__(self) -> None:
        self.provider = settings.embedding_provider
        self.dimensions = settings.embedding_dimensions
        self._client = None
        if self.provider == "openai" and settings.openai_api_key and OpenAI is not None:
            self._client = OpenAI(api_key=settings.openai_api_key)

    def embed_text(self, text: str) -> list[float]:
        if self._client is not None:
            try:
                response = self._client.embeddings.create(
                    model=settings.embedding_model,
                    input=text,
                )
                return list(response.data[0].embedding)
            except Exception:
                pass
        return self._fallback_embedding(text)

    def cosine_similarity(self, left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        numerator = sum(l * r for l, r in zip(left, right))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return numerator / (left_norm * right_norm)

    def _fallback_embedding(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
            slot = int(digest[:8], 16) % self.dimensions
            sign = -1.0 if int(digest[8:10], 16) % 2 else 1.0
            vector[slot] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]
