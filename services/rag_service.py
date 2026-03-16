from __future__ import annotations

import json
import re
from pathlib import Path

from config import settings
from models import PolicyDocument, RetrievalMatch
from state import store


class RagService:
    def __init__(self, embedding_service) -> None:
        self.embedding_service = embedding_service
        self.index_dir = Path(__file__).resolve().parent.parent / "data" / "vector_index"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.index_dir / "policy_chunks.json"
        self._chunk_cache: list[dict] = []
        self._ensure_index()

    def retrieve(self, query: str, limit: int = 3, product_hint: str | None = None) -> list[RetrievalMatch]:
        self._ensure_index()
        query_embedding = self.embedding_service.embed_text(query)
        query_tokens = set(self._tokenize(query))

        scored: list[RetrievalMatch] = []
        for chunk in self._chunk_cache:
            cosine = self.embedding_service.cosine_similarity(query_embedding, chunk["embedding"])
            overlap = len(query_tokens.intersection(chunk["tokens"]))
            overlap_bonus = min(overlap * 0.05, 0.2)
            hint_bonus = 0.12 if product_hint and chunk["product"].lower() == product_hint.lower() else 0.0
            score = cosine + overlap_bonus + hint_bonus
            scored.append(
                RetrievalMatch(
                    chunk_id=chunk["chunk_id"],
                    policy_id=chunk["policy_id"],
                    product=chunk["product"],
                    title=chunk["title"],
                    text=chunk["text"],
                    score=round(score, 4),
                )
            )

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:limit]

    def get_policy_for_product(self, product: str) -> PolicyDocument | None:
        for policy in store.policies:
            if policy.product.lower() == product.lower():
                return policy
        return None

    def get_policy_by_id(self, policy_id: str) -> PolicyDocument | None:
        for policy in store.policies:
            if policy.policy_id == policy_id:
                return policy
        return None

    def _ensure_index(self) -> None:
        current_signature = self._policy_signature()
        if self.index_path.exists():
            with self.index_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
            if payload.get("signature") == current_signature:
                self._chunk_cache = payload.get("chunks", [])
                return

        chunks = self._build_chunk_records()
        payload = {
            "signature": current_signature,
            "embedding_provider": self.embedding_service.provider,
            "embedding_model": settings.embedding_model,
            "chunks": chunks,
        }
        with self.index_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)
        self._chunk_cache = chunks

    def _build_chunk_records(self) -> list[dict]:
        chunks: list[dict] = []
        for policy in store.policies:
            chunk_texts = self._chunk_policy(policy)
            for index, text in enumerate(chunk_texts, start=1):
                chunk_id = f"{policy.policy_id}-chunk-{index}"
                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "policy_id": policy.policy_id,
                        "product": policy.product,
                        "title": policy.title,
                        "text": text,
                        "tokens": self._tokenize(text),
                        "embedding": self.embedding_service.embed_text(
                            f"{policy.product}\n{policy.title}\n{text}"
                        ),
                    }
                )
        return chunks

    def _chunk_policy(self, policy: PolicyDocument) -> list[str]:
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", policy.policy_text)
            if sentence.strip()
        ]
        if not sentences:
            return [policy.policy_text]

        chunks: list[str] = []
        current: list[str] = []
        current_length = 0
        target_length = 240
        overlap_sentences = 1

        for sentence in sentences:
            sentence_length = len(sentence)
            if current and current_length + sentence_length > target_length:
                chunks.append(" ".join(current))
                current = current[-overlap_sentences:]
                current_length = sum(len(item) for item in current)
            current.append(sentence)
            current_length += sentence_length

        if current:
            chunks.append(" ".join(current))
        return chunks

    def _policy_signature(self) -> str:
        joined = "|".join(f"{policy.policy_id}:{policy.policy_text}" for policy in store.policies)
        return str(hash(joined))

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())
