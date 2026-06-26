"""Milvus 向量库连接与集合管理 (dense 检索)。

集合 schema: id(int64, 与 Postgres chunks.id 对齐) + embedding(float_vector) + document_id + chunk_index。
索引: HNSW + COSINE。
"""
from __future__ import annotations

from functools import lru_cache

from pymilvus import (
    CollectionSchema,
    DataType,
    FieldSchema,
    MilvusClient,
)

from app.config import settings


@lru_cache
def get_client() -> MilvusClient:
    return MilvusClient(uri=settings.milvus_uri)


def ensure_collection() -> None:
    client = get_client()
    name = settings.milvus_collection
    if client.has_collection(name):
        return
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.embed_dim),
        FieldSchema(name="document_id", dtype=DataType.INT64),
        FieldSchema(name="chunk_index", dtype=DataType.INT64),
    ]
    schema = CollectionSchema(fields, description="nexora chunk embeddings")
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        index_type="HNSW",
        metric_type="COSINE",
        params={"M": 16, "efConstruction": 64},
    )
    client.create_collection(name, schema=schema, index_params=index_params)


def insert_embeddings(rows: list[dict]) -> int:
    """rows: [{id, embedding, document_id, chunk_index}]"""
    if not rows:
        return 0
    ensure_collection()
    client = get_client()
    client.insert(settings.milvus_collection, rows)
    return len(rows)


def search(query_embedding: list[float], top_k: int) -> list[dict]:
    """返回 [{id, document_id, chunk_index, distance}]。"""
    client = get_client()
    if not client.has_collection(settings.milvus_collection):
        return []
    res = client.search(
        settings.milvus_collection,
        data=[query_embedding],
        limit=top_k,
        output_fields=["document_id", "chunk_index"],
        search_params={"metric_type": "COSINE", "params": {"ef": 64}},
    )
    hits = res[0] if res else []
    out = []
    for h in hits:
        ent = h.get("entity", {})
        out.append(
            {
                "id": h["id"],
                "document_id": ent.get("document_id"),
                "chunk_index": ent.get("chunk_index"),
                "distance": h.get("distance", 0.0),
            }
        )
    return out


def delete_document(document_id: int) -> None:
    client = get_client()
    if client.has_collection(settings.milvus_collection):
        client.delete(settings.milvus_collection, filter=f"document_id == {document_id}")


def count() -> int:
    client = get_client()
    if not client.has_collection(settings.milvus_collection):
        return 0
    try:
        return client.get_collection_stats(settings.milvus_collection)["row_count"]
    except Exception:  # noqa: BLE001
        return -1
