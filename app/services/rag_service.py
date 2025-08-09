"""
Async RAG service built with LangChain vector store and a simple LangGraph-style node graph.

This service demonstrates:
- Vector store ingestion and retrieval (FAISS + sentence-transformers)
- A node graph pipeline for retrieval → synthesis → postprocess
- Integration with existing AsyncAIService for generation

Notes:
- Uses in-memory FAISS indices keyed by corpus_id
- Designed to be lightweight and Railway-friendly
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

LANGCHAIN_AVAILABLE = True
HuggingFaceEmbeddings = None
FAISS = None
RecursiveCharacterTextSplitter = None

# Embeddings and vector store (langchain-community)
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings as _HFEmb
    from langchain_community.vectorstores import FAISS as _FAISS
    HuggingFaceEmbeddings = _HFEmb
    FAISS = _FAISS
except Exception:
    LANGCHAIN_AVAILABLE = False

# Text splitter (new package in LC 0.2+, fallback to legacy import)
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter as _RCTextSplitter
    RecursiveCharacterTextSplitter = _RCTextSplitter
except Exception:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter as _RCTextSplitter
        RecursiveCharacterTextSplitter = _RCTextSplitter
    except Exception:
        LANGCHAIN_AVAILABLE = False


@dataclass
class RAGNodeResult:
    name: str
    started_at: float
    finished_at: float
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]


class AsyncRAGService:
    """RAG service with ingestion, query preprocessing, hybrid retrieval, and synthesis."""
    @dataclass
    class CorpusIndex:
        vectorstore: Any
        tfidf_vectorizer: Optional[TfidfVectorizer]
        tfidf_matrix: Optional[np.ndarray]
        chunks: List[Dict[str, Any]]

    def __init__(self, ai_service, cache_service=None):
        self.ai_service = ai_service
        self.cache_service = cache_service
        self._corpus_to_index: Dict[str, AsyncRAGService.CorpusIndex] = {}
        self._embeddings = None
        self._text_splitter = None

    async def _ensure_components(self):
        if not LANGCHAIN_AVAILABLE:
            raise RuntimeError("LangChain components are not available. Ensure dependencies are installed.")
        if self._embeddings is None:
            # Small, efficient model suitable for Railway free-tier
            self._embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        if self._text_splitter is None:
            self._text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=120,
                separators=["\n\n", "\n", ". ", ".", "?", "!", ",", " "]
            )

    async def ingest(self, corpus_id: str, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Ingest raw texts into indexes (vector + lexical) keyed by corpus_id."""
        await self._ensure_components()

        if not texts:
            raise ValueError("No texts provided for ingestion")

        documents = []
        for idx, text in enumerate(texts):
            metadata = (metadatas[idx] if metadatas and idx < len(metadatas) else {}) or {}
            documents.append({"page_content": text, "metadata": metadata})

        # Split documents into chunks
        split_docs: List[Dict[str, Any]] = []
        for doc in documents:
            for chunk in self._text_splitter.split_text(doc["page_content"]):
                split_docs.append({"page_content": chunk, "metadata": doc["metadata"]})

        # Build or update both FAISS and TF-IDF indexes
        if corpus_id in self._corpus_to_index:
            corpus_index = self._corpus_to_index[corpus_id]
            # Update vector index
            corpus_index.vectorstore.add_texts(
                texts=[d["page_content"] for d in split_docs],
                metadatas=[d["metadata"] for d in split_docs]
            )
            # Update lexical index (refit for simplicity)
            all_chunks = corpus_index.chunks + split_docs
            vectorizer = TfidfVectorizer(stop_words='english', max_features=50000)
            tfidf_matrix = vectorizer.fit_transform([c["page_content"] for c in all_chunks])
            corpus_index.tfidf_vectorizer = vectorizer
            corpus_index.tfidf_matrix = tfidf_matrix
            corpus_index.chunks = all_chunks
        else:
            vectorstore = FAISS.from_texts(
                texts=[d["page_content"] for d in split_docs],
                embedding=self._embeddings,
                metadatas=[d["metadata"] for d in split_docs]
            )
            vectorizer = TfidfVectorizer(stop_words='english', max_features=50000)
            tfidf_matrix = vectorizer.fit_transform([d["page_content"] for d in split_docs])
            self._corpus_to_index[corpus_id] = AsyncRAGService.CorpusIndex(
                vectorstore=vectorstore,
                tfidf_vectorizer=vectorizer,
                tfidf_matrix=tfidf_matrix,
                chunks=split_docs
            )

        return {
            "success": True,
            "corpus_id": corpus_id,
            "chunks_indexed": len(split_docs)
        }

    def _preprocess_query(self, query: str) -> str:
        return (query or "").strip()

    async def _retrieve_vector(self, corpus_id: str, query: str, k: int = 4) -> List[Dict[str, Any]]:
        await self._ensure_components()
        if corpus_id not in self._corpus_to_index:
            raise ValueError(f"Corpus '{corpus_id}' not found. Ingest documents first.")
        vectorstore: FAISS = self._corpus_to_index[corpus_id].vectorstore
        docs_and_scores = vectorstore.similarity_search_with_score(query, k=k)
        results: List[Dict[str, Any]] = []
        for doc, score in docs_and_scores:
            results.append({
                "content": doc.page_content,
                "metadata": getattr(doc, "metadata", {}) or {},
                "score": float(score),
                "score_type": "vector"
            })
        return results

    async def _retrieve_lexical(self, corpus_id: str, query: str, k: int = 4) -> List[Dict[str, Any]]:
        if corpus_id not in self._corpus_to_index:
            raise ValueError(f"Corpus '{corpus_id}' not found. Ingest documents first.")
        corpus_index = self._corpus_to_index[corpus_id]
        if not corpus_index.tfidf_vectorizer or corpus_index.tfidf_matrix is None:
            return []
        q_vec = corpus_index.tfidf_vectorizer.transform([query])
        sims = cosine_similarity(q_vec, corpus_index.tfidf_matrix).ravel()
        top_idx = np.argsort(-sims)[:k]
        results: List[Dict[str, Any]] = []
        for i in top_idx:
            chunk = corpus_index.chunks[int(i)]
            results.append({
                "content": chunk["page_content"],
                "metadata": chunk.get("metadata", {}) or {},
                "score": float(sims[int(i)]),
                "score_type": "lexical"
            })
        return results

    async def _retrieve_hybrid(self, corpus_id: str, query: str, k: int = 4, alpha: float = 0.5) -> List[Dict[str, Any]]:
        vec = await self._retrieve_vector(corpus_id, query, k=max(k, 8))
        lex = await self._retrieve_lexical(corpus_id, query, k=max(k, 8))

        def normalize(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            if not items:
                return items
            scores = np.array([it["score"] for it in items], dtype=float)
            # Heuristic: FAISS distance vs similarity
            if any(s > 1.5 for s in scores):
                sim = 1.0 / (1.0 + scores)
            else:
                sim = scores
            min_v, max_v = float(sim.min()), float(sim.max())
            if max_v - min_v < 1e-9:
                norm = np.ones_like(sim)
            else:
                norm = (sim - min_v) / (max_v - min_v)
            out = []
            for it, s in zip(items, norm):
                it2 = dict(it)
                it2["norm_score"] = float(s)
                out.append(it2)
            return out

        vec_n = normalize(vec)
        lex_n = normalize(lex)

        merged: Dict[str, Dict[str, Any]] = {}
        for it in vec_n:
            key = str(hash(it["content"]))
            merged[key] = it
        for it in lex_n:
            key = str(hash(it["content"]))
            if key in merged:
                merged[key]["hybrid_score"] = alpha * merged[key].get("norm_score", 0.0) + (1 - alpha) * float(it.get("norm_score", 0.0))
            else:
                it2 = dict(it)
                it2["hybrid_score"] = (1 - alpha) * float(it.get("norm_score", 0.0))
                merged[key] = it2

        for v in merged.values():
            if "hybrid_score" not in v:
                v["hybrid_score"] = alpha * v.get("norm_score", 0.0)

        ranked = sorted(merged.values(), key=lambda x: -x["hybrid_score"])[:k]
        for r in ranked:
            r.pop("norm_score", None)
        return ranked

    async def _synthesize(self, query: str, retrieved: List[Dict[str, Any]], model: str, temperature: float, max_tokens: int) -> str:
        """Use the existing AI service to generate an answer with citations."""
        context_blocks = []
        for i, item in enumerate(retrieved, start=1):
            meta = item.get("metadata", {})
            source = meta.get("source") or meta.get("title") or f"chunk-{i}"
            context_blocks.append(f"[Source {i}: {source}]\n{item['content']}")
        context_text = "\n\n".join(context_blocks)

        prompt = (
            "You are a senior strategy analyst. Answer the business question using the CONTEXT.\n"
            "Cite sources inline like [1], [2]. Then provide a JSON section with keys 'insights', 'risks', 'next_steps'.\n\n"
            f"QUESTION: {query}\n\nCONTEXT:\n{context_text}\n\n"
            "Return answer first, then a JSON block strictly.")

        result = await self.ai_service.chat(
            message=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return result.get("response", "")

    async def ask(self, *, corpus_id: str, question: str, k: int = 4, model: str = "mistral-small", temperature: float = 0.3, max_tokens: int = 800, search_mode: str = "hybrid") -> Dict[str, Any]:
        """Run the full workflow: preprocess → retrieve → augment+LLM → postprocess."""
        if not question:
            raise ValueError("Question is required")

        node_results: List[RAGNodeResult] = []

        # Node: preprocess
        t0 = time.time()
        q_norm = self._preprocess_query(question)
        t1 = time.time()
        node_results.append(RAGNodeResult(
            name="preprocess",
            started_at=t0,
            finished_at=t1,
            inputs={"raw_query": question},
            outputs={"normalized_query": q_norm}
        ))

        # Node: retrieve
        t2 = time.time()
        smode = (search_mode or "hybrid").lower()
        if smode == "vector":
            retrieved = await self._retrieve_vector(corpus_id, q_norm, k=k)
            rname = "retrieve_vector"
        elif smode == "lexical":
            retrieved = await self._retrieve_lexical(corpus_id, q_norm, k=k)
            rname = "retrieve_lexical"
        else:
            retrieved = await self._retrieve_hybrid(corpus_id, q_norm, k=k)
            rname = "retrieve_hybrid"
        t3 = time.time()
        node_results.append(RAGNodeResult(
            name=rname,
            started_at=t2,
            finished_at=t3,
            inputs={"k": k, "search_mode": smode},
            outputs={"num_chunks": len(retrieved)}
        ))

        # Node: synthesize (augment prompt and generate)
        t4 = time.time()
        answer = await self._synthesize(q_norm, retrieved, model=model, temperature=temperature, max_tokens=max_tokens)
        t5 = time.time()
        node_results.append(RAGNodeResult(
            name="synthesize",
            started_at=t4,
            finished_at=t5,
            inputs={"model": model, "temperature": temperature, "max_tokens": max_tokens},
            outputs={"answer_preview": answer[:120]}
        ))

        # Node: postprocess (extract JSON if present)
        insights: List[str] = []
        risks: List[str] = []
        next_steps: List[str] = []
        import json, re
        json_block = None
        match = re.search(r"\{[\s\S]*\}$", answer.strip())
        if match:
            try:
                json_block = json.loads(match.group(0))
                insights = list(json_block.get("insights", []) or [])
                risks = list(json_block.get("risks", []) or [])
                next_steps = list(json_block.get("next_steps", []) or [])
            except Exception:
                json_block = None
        t6 = time.time()
        node_results.append(RAGNodeResult(
            name="postprocess",
            started_at=t5,
            finished_at=t6,
            inputs={},
            outputs={
                "has_json": bool(json_block),
                "insights_count": len(insights),
                "risks_count": len(risks),
                "next_steps_count": len(next_steps),
            }
        ))

        # Build citations list
        sources: List[Dict[str, Any]] = []
        for idx, item in enumerate(retrieved, start=1):
            meta = item.get("metadata", {})
            sources.append({
                "id": idx,
                "title": meta.get("title") or meta.get("source") or f"Document {idx}",
                "score": item.get("score"),
                "metadata": meta,
                "preview": item.get("content", "")[:200]
            })

        return {
            "success": True,
            "answer": answer,
            "insights": insights,
            "risks": risks,
            "next_steps": next_steps,
            "sources": sources,
            "graph": self.get_graph_definition(),
            "timings": {
                n.name: round(n.finished_at - n.started_at, 4) for n in node_results
            }
        }

    def get_graph_definition(self) -> Dict[str, Any]:
        """Return a schema matching the requested workflow."""
        return {
            "nodes": [
                {"id": "preprocess", "label": "Query Preprocessing", "type": "pre"},
                {"id": "retrieve_hybrid", "label": "Retriever (Hybrid)", "type": "retriever"},
                {"id": "synthesize", "label": "Augment + LLM", "type": "llm"},
                {"id": "postprocess", "label": "Response", "type": "parser"},
            ],
            "edges": [
                {"from": "preprocess", "to": "retrieve_hybrid"},
                {"from": "retrieve_hybrid", "to": "synthesize"},
                {"from": "synthesize", "to": "postprocess"},
            ]
        }


