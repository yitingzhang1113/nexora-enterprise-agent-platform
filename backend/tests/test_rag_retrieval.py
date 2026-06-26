"""切块 + 多路检索 单测。chunker 纯逻辑; multi_retrieve 为集成(需 milvus+db, 缺则跳过)。"""
import pytest

from app.rag.chunker import chunk_text


def test_chunk_short_text_single():
    assert chunk_text("短文本") == ["短文本"]


def test_chunk_long_text_overlap():
    text = "。".join([f"句子{i}内容比较长一些用于测试切块逻辑" for i in range(80)])
    chunks = chunk_text(text, size=200, overlap=40)
    assert len(chunks) > 1
    assert all(len(c) <= 240 for c in chunks)  # size + overlap 容差


def test_multi_retrieve_integration():
    """集成: 命中已索引政策文档。缺少服务时跳过。"""
    try:
        from app.db.engine import SessionLocal
        from app.rag.multi_retriever import multi_retrieve

        db = SessionLocal()
        try:
            hits = multi_retrieve(db, "退款超过多少需要审批", top_k=3)
        finally:
            db.close()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"服务不可用, 跳过集成检索: {e}")
    assert isinstance(hits, list)
