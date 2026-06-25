"""种子脚本：预置「医药知识助手」persona + 索引示例药品资料。

用法 (容器内或本地):
    python -m seed.seed
幂等：重复运行会跳过已存在的同名 persona，但会重复索引文档 (演示足够)。
"""
from __future__ import annotations

import glob
import os

from app.connectors.file_upload import FileUploadConnector
from app.db.base import SessionLocal
from app.indexing.pipeline import run_indexing
from app.models import Connector, IndexAttempt, Persona, SourceType

PHARMA_SYSTEM_PROMPT = (
    "你是「医药知识助手」，面向医药从业者与学习者。"
    "请严格依据检索到的【参考资料】回答，涉及剂量、禁忌、相互作用时务必谨慎，"
    "并在句末用 [n] 标注引用编号。"
    "如资料未覆盖，请明确说明并提示『请遵医嘱』，绝不编造剂量或适应症。"
)

SEED_DIR = os.path.dirname(__file__)
DOCS_GLOB = os.path.join(SEED_DIR, "docs", "*.md")


def seed_persona(db) -> None:
    exists = db.query(Persona).filter(Persona.name == "医药知识助手").first()
    if exists:
        print("persona 已存在，跳过")
        return
    persona = Persona(
        name="医药知识助手",
        description="基于内部药品资料的问答助手 (演示)",
        system_prompt=PHARMA_SYSTEM_PROMPT,
        tools=["search_docs", "calculator"],
    )
    db.add(persona)
    db.commit()
    print(f"已创建 persona: {persona.name} (id={persona.id})")


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
    attempt = run_indexing(db, conn, connector_id=connector.id, attempt=attempt)
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
