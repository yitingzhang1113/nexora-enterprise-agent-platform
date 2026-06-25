"""种子脚本 (v2): 医药助手 persona + 索引示例药品资料到 OpenSearch。

用法 (容器内): python -m seed.seed
依赖: postgres / opensearch / model_server / ollama 均已就绪。
"""
from __future__ import annotations

import glob
import os

from nexora.connectors.file_upload.connector import FileUploadConnector
from nexora.db.engine import SessionLocal
from nexora.db.models import Connector, IndexAttempt, Persona, SourceType
from nexora.indexing.indexing_pipeline import run_indexing

PHARMA_SYSTEM_PROMPT = (
    "你是「医药知识助手」, 面向医药从业者与学习者。"
    "请严格依据检索到的【参考资料】回答, 涉及剂量、禁忌、相互作用时务必谨慎, "
    "并在句末用 [n] 标注引用编号。"
    "如资料未覆盖, 请明确说明并提示『请遵医嘱』, 绝不编造剂量或适应症。"
)

SEED_DIR = os.path.dirname(__file__)
DOCS_GLOB = os.path.join(SEED_DIR, "docs", "*.md")


def seed_persona(db) -> None:
    if db.query(Persona).filter(Persona.name == "医药知识助手").first():
        print("persona 已存在, 跳过")
        return
    p = Persona(
        name="医药知识助手",
        description="基于内部药品资料的问答助手 (演示)",
        system_prompt=PHARMA_SYSTEM_PROMPT,
        tools=["search_docs", "calculator"],
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
        name="seed-pharma-docs",
        source=SourceType.file_upload,
        config={"filenames": [os.path.basename(p) for p in paths]},
    )
    db.add(connector)
    db.flush()
    attempt = IndexAttempt(connector_id=connector.id)
    db.add(attempt)
    db.commit()

    conn = FileUploadConnector(file_paths=paths, titles=[os.path.basename(p) for p in paths])
    attempt = run_indexing(db, conn, connector.id, attempt)
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
