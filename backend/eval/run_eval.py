"""离线评测: Intent Accuracy / Tool Call Success / RAG Recall@3。

用法 (容器内): python -m eval.run_eval
直接调用内部模块 (不打满 LLM 生成), 需 DB/Milvus 就绪 (Recall/Tool 用)。
"""
from __future__ import annotations

import json
import os

from app.graph.nodes import plan_tasks
from app.intent.classifier import classify_intent
from app.intent.intent_tree import extract_amount, extract_order_id, extract_sku

CASES = os.path.join(os.path.dirname(__file__), "eval_cases.jsonl")


def _plan_tools(query: str) -> set[str]:
    intent = classify_intent(query)
    state = {
        "intent": intent, "question": query, "rewritten_query": query,
        "sku": extract_sku(query), "order_id": extract_order_id(query),
        "amount": extract_amount(query),
    }
    return {p["tool"] for p in plan_tasks(state)["plan"]}


def main() -> None:
    cases = [json.loads(l) for l in open(CASES, encoding="utf-8") if l.strip()]

    intent_total = intent_ok = 0
    tool_total = tool_ok = 0
    recall_total = recall_ok = 0

    for c in cases:
        if "expected_intent" in c:
            intent_total += 1
            got = classify_intent(c["query"])
            ok = got == c["expected_intent"]
            intent_ok += ok
            print(f"[intent] {'OK ' if ok else 'XX '} {c['query']} -> {got} (exp {c['expected_intent']})")
        if "expected_tool" in c:
            tool_total += 1
            tools = _plan_tools(c["query"])
            ok = c["expected_tool"] in tools
            tool_ok += ok
            print(f"[tool]   {'OK ' if ok else 'XX '} {c['query']} -> {sorted(tools)}")
        if "expected_doc" in c:
            recall_total += 1
            try:
                from app.db.engine import SessionLocal
                from app.rag.multi_retriever import multi_retrieve

                db = SessionLocal()
                try:
                    hits = multi_retrieve(db, c["query"], top_k=3)
                finally:
                    db.close()
                titles = [h.doc_title for h in hits]
                ok = c["expected_doc"] in titles
            except Exception as e:  # noqa: BLE001
                ok = False
                titles = [f"<error: {e}>"]
            recall_ok += ok
            print(f"[recall] {'OK ' if ok else 'XX '} {c['query']} -> {titles}")

    print("\n==== Metrics ====")
    if intent_total:
        print(f"Intent Accuracy : {intent_ok}/{intent_total} = {intent_ok/intent_total:.0%}")
    if tool_total:
        print(f"Tool Call Hit   : {tool_ok}/{tool_total} = {tool_ok/tool_total:.0%}")
    if recall_total:
        print(f"RAG Recall@3    : {recall_ok}/{recall_total} = {recall_ok/recall_total:.0%}")


if __name__ == "__main__":
    main()
