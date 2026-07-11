from __future__ import annotations

from typing import Any

from domains.rag.models import Document, RagAnswer
from intelligence.rag.embeddings import EmbeddingService
from intelligence.rag.retrieval import RetrievalService


class RagService:
    """Full RAG pipeline: embed → retrieve → generate answer with citations."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        retrieval_service: RetrievalService,
        llm_service: Any = None,
    ):
        self.embeddings = embedding_service
        self.retrieval = retrieval_service
        self._llm = llm_service

    @property
    def llm(self):
        if self._llm is None:
            from intelligence.agents.llm import LLMService
            self._llm = LLMService()
        return self._llm

    async def answer(
        self,
        question: str,
        tenant_id: str,
        context_sources: list[str] | None = None,
        top_k: int = 5,
        min_score: float = 0.7,
    ) -> RagAnswer:
        query_embedding = await self.embeddings.embed_text(question)
        if not query_embedding:
            return RagAnswer(answer="", citations=[], chunks_used=0, confidence=0.0)

        results = await self.retrieval.retrieve(
            query_embedding=query_embedding,
            tenant_id=tenant_id,
            top_k=top_k,
            min_score=min_score,
        )

        if not results:
            return RagAnswer(
                answer="لم يتم العثور على معلومات كافية للإجابة على هذا السؤال.",
                citations=[],
                chunks_used=0,
                confidence=0.0,
            )

        context_parts: list[str] = []
        citations: list[dict[str, Any]] = []
        seen_sources: set[str] = set()

        for r in results:
            context_parts.append(r.chunk.content)
            if r.source and r.source.id not in seen_sources:
                seen_sources.add(r.source.id)
                citations.append({
                    "document_id": r.source.id,
                    "title": r.source.title,
                    "source_type": r.source.source_type,
                    "source_id": r.source.source_id,
                    "score": round(r.score, 4),
                })

        context = "\n\n".join(context_parts)
        system_prompt = (
            "أنت مساعد ذكي لتحليل بيانات المبيعات. استخدم المعلومات التالية للإجابة على سؤال المستخدم. "
            "إذا كانت المعلومات غير كافية، قل أنك لا تملك معلومات كافية. "
            "قم بتضمين المصادر المستخدمة في الإجابة كلما أمكن."
        )
        user_prompt = f"المعلومات المتاحة:\n\n{context}\n\nالسؤال: {question}"

        try:
            response = await self.llm.chat(system=system_prompt, messages=[{"role": "user", "content": user_prompt}])
            answer_text = response.content
            confidence = min(1.0, len(results) / top_k)
        except Exception:
            answer_text = context_parts[0][:500] if context_parts else ""
            confidence = 0.3

        return RagAnswer(
            answer=answer_text,
            citations=citations,
            chunks_used=len(results),
            confidence=confidence,
        )

    async def generate_brief(
        self,
        entity_id: str,
        entity_type: str,
        tenant_id: str,
    ) -> RagAnswer:
        results = await self.retrieval.retrieve_by_source(
            source_type=entity_type, source_id=entity_id
        )

        if not results:
            return RagAnswer(
                answer="",
                citations=[],
                chunks_used=0,
                confidence=0.0,
            )

        context_parts: list[str] = []
        citations: list[dict[str, Any]] = []

        for r in results:
            context_parts.append(r.chunk.content)
            if r.source:
                citations.append({
                    "document_id": r.source.id,
                    "title": r.source.title,
                    "source_type": r.source.source_type,
                    "source_id": r.source.source_id,
                })

        context = "\n\n".join(context_parts)

        system_prompt = (
            "أنت مساعد ذكي لإعداد ملخصات سياقية. قم بتلخيص المعلومات التالية في فقرة موجزة "
            "تغطي النقاط الرئيسية والمعلومات الهامة."
        )
        user_prompt = f"المعلومات:\n\n{context}"

        try:
            response = await self.llm.chat(system=system_prompt, messages=[{"role": "user", "content": user_prompt}])
            answer_text = response.content
        except Exception:
            answer_text = context[:1000]

        return RagAnswer(
            answer=answer_text,
            citations=citations,
            chunks_used=len(results),
            confidence=0.8 if results else 0.0,
        )
