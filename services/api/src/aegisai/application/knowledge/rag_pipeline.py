from __future__ import annotations

from dataclasses import dataclass

from .llm_gateway import LLMGateway, LLMResponse
from .vector_memory import MemoryDocument, SQLiteVectorMemoryStore


@dataclass(frozen=True)
class RAGResult:
    answer: LLMResponse
    retrieved_documents: tuple[MemoryDocument, ...]
    scores: tuple[float, ...]


class RAGPipeline:
    """Retrieval-augmented generation pipeline for agent policy/context grounding."""

    def __init__(
        self,
        memory_store: SQLiteVectorMemoryStore | None = None,
        llm_gateway: LLMGateway | None = None,
    ) -> None:
        self.memory_store = memory_store or SQLiteVectorMemoryStore()
        self.llm_gateway = llm_gateway or LLMGateway()

    def answer(
        self,
        tenant_id: str,
        namespace: str,
        query: str,
        limit: int = 3,
    ) -> RAGResult:
        retrieved = self.memory_store.search(tenant_id, namespace, query, limit=limit)
        context = "\n".join(
            f"- {document.source_uri}: {document.content}" for document, _score in retrieved
        )
        response = self.llm_gateway.complete(
            system_prompt="You are a governed enterprise AI agent. Use only retrieved policy context.",
            user_prompt=f"Question: {query}\nRetrieved context:\n{context}",
        )
        return RAGResult(
            answer=response,
            retrieved_documents=tuple(document for document, _score in retrieved),
            scores=tuple(score for _document, score in retrieved),
        )

