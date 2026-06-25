"""OpenSearch 实现的 DocumentIndex (替代 Onyx 的 Vespa)。

混合检索 = kNN(向量) + BM25(关键词) 两路, 应用层 RRF 融合。
content/title 用内置 `cjk` 分析器, 让中文也能走关键词召回 (修复 v1 中文 FTS 痛点)。
"""
from __future__ import annotations

from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk

from nexora.configs.app_configs import settings
from nexora.document_index.interfaces import DocumentIndex
from nexora.document_index.models import IndexChunk, InferenceChunk

RRF_K = 60


class OpenSearchDocumentIndex(DocumentIndex):
    def __init__(self, index_name: str | None = None, embed_dim: int | None = None) -> None:
        self.index_name = index_name or settings.opensearch_index
        self.embed_dim = embed_dim or settings.embed_dim
        self.client = OpenSearch(hosts=[settings.opensearch_url], timeout=30)

    # ---------- setup ----------
    def ensure_setup(self) -> None:
        if self.client.indices.exists(self.index_name):
            return
        body = {
            "settings": {
                "index": {"knn": True, "number_of_shards": 1, "number_of_replicas": 0},
                "analysis": {"analyzer": {"default": {"type": "cjk"}}},
            },
            "mappings": {
                "properties": {
                    "document_id": {"type": "long"},
                    "chunk_index": {"type": "integer"},
                    "source": {"type": "keyword"},
                    "link": {"type": "keyword"},
                    "title": {"type": "text", "analyzer": "cjk"},
                    "content": {"type": "text", "analyzer": "cjk"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": self.embed_dim,
                        "method": {
                            "name": "hnsw",
                            "engine": "lucene",
                            "space_type": "cosinesimil",
                        },
                    },
                }
            },
        }
        self.client.indices.create(self.index_name, body=body)

    # ---------- write ----------
    def index(self, chunks: list[IndexChunk]) -> int:
        if not chunks:
            return 0
        self.ensure_setup()
        actions = [
            {
                "_index": self.index_name,
                "_id": f"{c.document_id}_{c.chunk_index}",
                "_source": c.to_os_doc(self.embed_dim),
            }
            for c in chunks
        ]
        success, _ = bulk(self.client, actions, refresh=True)
        return success

    def delete_document(self, document_id: int) -> None:
        if not self.client.indices.exists(self.index_name):
            return
        self.client.delete_by_query(
            self.index_name,
            body={"query": {"term": {"document_id": document_id}}},
            refresh=True,
        )

    # ---------- read ----------
    def hybrid_retrieval(
        self, query: str, query_embedding: list[float], top_k: int
    ) -> list[InferenceChunk]:
        if not self.client.indices.exists(self.index_name):
            return []
        pool = max(top_k * 4, 20)

        knn_hits = self.client.search(
            index=self.index_name,
            body={
                "size": pool,
                "query": {"knn": {"embedding": {"vector": query_embedding, "k": pool}}},
                "_source": {"excludes": ["embedding"]},
            },
        )["hits"]["hits"]

        bm25_hits = self.client.search(
            index=self.index_name,
            body={
                "size": pool,
                "query": {"multi_match": {"query": query, "fields": ["content", "title^1.5"]}},
                "_source": {"excludes": ["embedding"]},
            },
        )["hits"]["hits"]

        return self._rrf_fuse(knn_hits, bm25_hits, top_k)

    def count(self) -> int:
        if not self.client.indices.exists(self.index_name):
            return 0
        return self.client.count(index=self.index_name)["count"]

    # ---------- RRF ----------
    @staticmethod
    def _rrf_fuse(knn_hits: list, bm25_hits: list, top_k: int) -> list[InferenceChunk]:
        vec_rank = {h["_id"]: i + 1 for i, h in enumerate(knn_hits)}
        kw_rank = {h["_id"]: i + 1 for i, h in enumerate(bm25_hits)}
        src_by_id: dict[str, dict] = {}
        for h in knn_hits + bm25_hits:
            src_by_id[h["_id"]] = h["_source"]

        fused: list[InferenceChunk] = []
        for cid, src in src_by_id.items():
            vr = vec_rank.get(cid)
            kr = kw_rank.get(cid)
            score = 0.0
            if vr:
                score += 1.0 / (RRF_K + vr)
            if kr:
                score += 1.0 / (RRF_K + kr)
            fused.append(
                InferenceChunk(
                    chunk_id=cid,
                    document_id=src["document_id"],
                    document_title=src.get("title", ""),
                    chunk_index=src.get("chunk_index", 0),
                    content=src.get("content", ""),
                    link=src.get("link") or None,
                    score=round(score, 6),
                    vector_rank=vr,
                    keyword_rank=kr,
                )
            )
        fused.sort(key=lambda c: c.score, reverse=True)
        return fused[:top_k]
