"""LangGraph 节点实现。

每个节点接收 state, 返回要合并进 state 的 partial dict。
DB 访问在节点内开短连接 (SessionLocal)。
"""
from __future__ import annotations

from app.db.engine import SessionLocal
from app.intent.classifier import classify_intent
from app.intent.clarification import make_clarification
from app.memory import store
from app.memory.short_term import get_recent
from app.models.llm_router import get_fast_llm, get_main_llm, record_failure, record_success
from app.rag.multi_retriever import multi_retrieve
from app.rag.prompt_builder import DEFAULT_SYSTEM, build_context
from app.rag.reranker import rerank
from app.tools import mcp_client

_ROLE_MAP = {"system": "system", "user": "human", "assistant": "ai", "tool": "human"}


def _to_lc(messages: list[dict]) -> list[tuple[str, str]]:
    return [(_ROLE_MAP.get(m["role"], "human"), m["content"]) for m in messages]


# ---------- 1. load_memory ----------
def load_memory(state: dict) -> dict:
    sid = state.get("session_id")
    history: list[dict] = []
    summary = None
    if sid:
        history = get_recent(sid, 6)
        db = SessionLocal()
        try:
            if not history:
                history = store.load_db_history(db, sid, 6)
            summary = store.get_summary(db, sid)
        finally:
            db.close()
    return {"history": history, "summary": summary}


# ---------- 2. rewrite_query ----------
def rewrite_query(state: dict) -> dict:
    q = state["question"]
    history = state.get("history") or []
    if not history:
        return {"rewritten_query": q}
    convo = "\n".join(f"{m['role']}: {m['content']}" for m in history[-4:])
    prompt = (
        "结合下面的对话历史, 把用户最新问题改写成一个**独立、完整、可直接检索**的问题"
        "(补全指代与省略)。只输出改写后的问题。\n\n"
        f"历史:\n{convo}\n\n最新问题: {q}\n改写:"
    )
    try:
        resp = get_fast_llm().invoke(prompt)
        rewritten = (getattr(resp, "content", "") or "").strip()
        return {"rewritten_query": rewritten or q}
    except Exception:  # noqa: BLE001
        return {"rewritten_query": q}


# ---------- 3. classify_intent ----------
def classify_intent_node(state: dict) -> dict:
    intent = classify_intent(state.get("rewritten_query") or state["question"], state.get("history"))
    return {"intent": intent}


# ---------- 4a. retrieve_docs ----------
def retrieve_docs(state: dict) -> dict:
    db = SessionLocal()
    try:
        chunks = multi_retrieve(db, state.get("rewritten_query") or state["question"])
    finally:
        db.close()
    return {"retrieved": chunks}


# ---------- 5. rerank ----------
def rerank_node(state: dict) -> dict:
    chunks = state.get("retrieved") or []
    reranked = rerank(state.get("rewritten_query") or state["question"], chunks)
    context, citations = build_context(reranked)
    return {"reranked": reranked, "context": context, "citations": citations}


# ---------- 4b. call_tools ----------
def call_tools(state: dict) -> dict:
    """让便宜模型选一个工具并给参数, 然后经 mcp_client 执行。"""
    q = state.get("rewritten_query") or state["question"]
    schemas = mcp_client.list_tools()
    tool_list = "\n".join(f"- {s['name']}: {s['description']}" for s in schemas)
    prompt = (
        "根据用户问题选择最合适的一个工具并给出 JSON 参数。"
        '只输出 JSON: {"tool": "<name>", "args": {...}}。\n\n'
        f"可用工具:\n{tool_list}\n\n用户问题: {q}\nJSON:"
    )
    import json
    import re

    tool_results: list[dict] = []
    try:
        resp = get_fast_llm().invoke(prompt)
        text = getattr(resp, "content", "") or ""
        m = re.search(r"\{.*\}", text, re.S)
        spec = json.loads(m.group(0)) if m else {}
        name = spec.get("tool", "")
        args = spec.get("args", {}) or {}
        output = mcp_client.call(name, args)
        tool_results.append({"name": name, "args": args, "output": output})
    except Exception as exc:  # noqa: BLE001
        tool_results.append({"name": "unknown", "args": {}, "output": f"工具调用失败: {exc}"})
    return {"tool_results": tool_results}


# ---------- 4c. clarify ----------
def clarify(state: dict) -> dict:
    text = make_clarification(state["question"])
    return {"clarification": text, "answer": text}


# ---------- 6. build_prompt ----------
def build_prompt(state: dict) -> dict:
    intent = state.get("intent", "knowledge_qa")
    system = state.get("persona_system") or DEFAULT_SYSTEM
    history = state.get("history") or []
    q = state["question"]

    if intent == "tool_call":
        results = state.get("tool_results") or []
        ctx = "\n".join(f"[{r['name']}] {r['output']}" for r in results)
        user = f"【工具结果】\n{ctx}\n\n【问题】\n{q}\n\n请基于工具结果用中文简洁作答。"
    elif intent == "chitchat":
        user = q
    else:  # knowledge_qa
        ctx = state.get("context", "")
        user = (
            f"【参考资料】\n{ctx}\n\n【问题】\n{q}\n\n请基于参考资料作答, 并标注引用编号 [n]。"
        )
    messages = [("system", system), *_to_lc(history), ("human", user)]
    return {"gen_messages": messages}


# ---------- 7. generate ----------
def generate(state: dict) -> dict:
    messages = state.get("gen_messages") or [("human", state["question"])]
    parts: list[str] = []
    try:
        for chunk in get_main_llm(streaming=True).stream(messages):
            parts.append(getattr(chunk, "content", "") or "")
        record_success()
    except Exception as exc:  # noqa: BLE001
        record_failure()
        parts.append(f"生成失败: {exc}")
    return {"answer": "".join(parts)}


# ---------- 8. save_memory ----------
def save_memory(state: dict) -> dict:
    sid = state.get("session_id")
    if sid:
        from app.memory.short_term import append_turn

        append_turn(sid, "user", state["question"])
        append_turn(sid, "assistant", state.get("answer", ""))
    return {}
