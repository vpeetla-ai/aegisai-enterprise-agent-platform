from __future__ import annotations

import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class MemoryDocument:
    document_id: str
    tenant_id: str
    namespace: str
    source_uri: str
    content: str
    embedding: tuple[float, ...]


class SQLiteVectorMemoryStore:
    """Small deterministic vector-memory reference store for agent retrieval."""

    def __init__(self, db_path: str | Path = ":memory:", dimensions: int = 32) -> None:
        self.dimensions = dimensions
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_documents (
              document_id TEXT PRIMARY KEY,
              tenant_id TEXT NOT NULL,
              namespace TEXT NOT NULL,
              source_uri TEXT NOT NULL,
              content TEXT NOT NULL,
              embedding TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_memory_tenant_namespace ON memory_documents(tenant_id, namespace)"
        )

    def add_document(
        self,
        tenant_id: str,
        namespace: str,
        source_uri: str,
        content: str,
    ) -> MemoryDocument:
        embedding = self.embed(content)
        document = MemoryDocument(
            document_id=f"mem-{uuid4()}",
            tenant_id=tenant_id,
            namespace=namespace,
            source_uri=source_uri,
            content=content,
            embedding=embedding,
        )
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO memory_documents (
                  document_id, tenant_id, namespace, source_uri, content, embedding
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    document.document_id,
                    tenant_id,
                    namespace,
                    source_uri,
                    content,
                    self._serialize(embedding),
                ),
            )
        return document

    def search(
        self,
        tenant_id: str,
        namespace: str,
        query: str,
        limit: int = 3,
    ) -> list[tuple[MemoryDocument, float]]:
        query_embedding = self.embed(query)
        rows = self.connection.execute(
            """
            SELECT * FROM memory_documents
            WHERE tenant_id = ? AND namespace = ?
            """,
            (tenant_id, namespace),
        ).fetchall()
        ranked: list[tuple[MemoryDocument, float]] = []
        for row in rows:
            embedding = self._deserialize(row["embedding"])
            document = MemoryDocument(
                document_id=row["document_id"],
                tenant_id=row["tenant_id"],
                namespace=row["namespace"],
                source_uri=row["source_uri"],
                content=row["content"],
                embedding=embedding,
            )
            ranked.append((document, self._cosine(query_embedding, embedding)))
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked[:limit]

    def seed_enterprise_memory(self, tenant_id: str = "bank-demo") -> None:
        self.add_document(
            tenant_id,
            "refund_policy",
            "policy://refund/thresholds",
            "Refunds over 1000 dollars require workflow-owner approval. Refunds over 10000 dollars require senior domain approval.",
        )
        self.add_document(
            tenant_id,
            "data_policy",
            "policy://data/restricted-deletion",
            "Restricted data deletion is irreversible and must be blocked unless compliance approves a documented exception.",
        )
        self.add_document(
            tenant_id,
            "communication_policy",
            "policy://customer-communications/regulated-topics",
            "Customer communications must not promise refunds, credits, legal outcomes, or deletion completion before approval.",
        )

    def count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS total FROM memory_documents").fetchone()
        return int(row["total"])

    def embed(self, text: str) -> tuple[float, ...]:
        vector = [0.0] * self.dimensions
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            bucket = sum(ord(char) for char in token) % self.dimensions
            vector[bucket] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return tuple(value / norm for value in vector)

    @staticmethod
    def _cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
        return sum(a * b for a, b in zip(left, right))

    @staticmethod
    def _serialize(vector: tuple[float, ...]) -> str:
        return ",".join(f"{value:.8f}" for value in vector)

    @staticmethod
    def _deserialize(value: str) -> tuple[float, ...]:
        return tuple(float(part) for part in value.split(",") if part)
