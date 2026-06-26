"""政策检索工具 (走 RAG / Milvus + BM25)。"""
from __future__ import annotations

from app.db.engine import SessionLocal
from app.rag.multi_retriever import multi_retrieve

POLICY_SCHEMA = {
    "name": "retrieve_policy",
    "description": "在政策知识库中检索相关条款 (退款/物流/库存/促销/风控等)。",
    "parameters": {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "政策相关问题"}},
        "required": ["query"],
    },
}


def retrieve_policy(query: str = "", **_) -> dict:
    db = SessionLocal()
    try:
        chunks = multi_retrieve(db, query)
        excerpts = []
        citations = []
        for i, c in enumerate(chunks, start=1):
            excerpts.append(f"[{i}] ({c.doc_title}) {c.content[:200]}")
            citations.append(
                {
                    "n": i, "chunk_id": c.chunk_id, "document_id": c.document_id,
                    "document_title": c.doc_title, "content": c.content, "link": c.link,
                }
            )
        return {"query": query, "excerpts": excerpts, "citations": citations}
    finally:
        db.close()
