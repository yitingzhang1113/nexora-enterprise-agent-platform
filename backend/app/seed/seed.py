"""种子脚本 (v3, 通用领域): 通用助手 persona + 索引示例文档到 Milvus + Postgres。

用法 (容器内): python -m app.seed.seed
依赖: postgres / milvus / model_server / ollama 就绪。
"""
from __future__ import annotations

import glob
import os

from app.db.engine import SessionLocal
from app.db.models import Connector, IndexAttempt, Persona, SourceType
from app.ingestion.indexer import index_raw_docs
from app.ingestion.parser import parse_file

SYSTEM_PROMPT = (
    "你是 Nexora 通用企业助手。优先依据检索到的【参考资料】回答, 并用 [n] 标注引用。"
    "若问题涉及天气/工单/销售等业务操作, 可使用相应工具; 资料不足时请如实说明。"
)

SEED_DIR = os.path.dirname(__file__)
DOCS_GLOB = os.path.join(SEED_DIR, "docs", "*.md")


def seed_persona(db) -> None:
    if db.query(Persona).filter(Persona.name == "通用助手").first():
        print("persona 已存在, 跳过")
        return
    p = Persona(
        name="通用助手",
        description="企业通用知识 + 业务工具助手 (演示)",
        system_prompt=SYSTEM_PROMPT,
        tools=["get_weather", "query_ticket", "query_sales"],
    )
    db.add(p)
    db.commit()
    print(f"已创建 persona: {p.name} (id={p.id})")


def seed_documents(db) -> None:
    paths = sorted(glob.glob(DOCS_GLOB))
    if not paths:
        print("未找到示例文档")
        return
    connector = Connector(
        name="seed-general-docs",
        source=SourceType.file_upload,
        config={"filenames": [os.path.basename(p) for p in paths]},
    )
    db.add(connector)
    db.flush()
    attempt = IndexAttempt(connector_id=connector.id)
    db.add(attempt)
    db.commit()
    raws = [parse_file(p, os.path.basename(p)) for p in paths]
    attempt = index_raw_docs(db, raws, attempt, connector.id)
    print(f"索引完成: status={attempt.status.value} chunks={attempt.num_chunks}")


def main() -> None:
    db = SessionLocal()
    try:
        seed_persona(db)
        seed_documents(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
