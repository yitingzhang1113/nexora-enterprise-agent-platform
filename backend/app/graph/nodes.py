"""LangGraph 节点 (v4 Ops Agent)。

load_memory → rewrite_query → classify_intent → plan_tasks → route
  → parallel_tool_calls → validate_result → human_approval_if_needed → execute_action → final_response
  (clarification / chitchat 走捷径)
"""
from __future__ import annotations

import asyncio
import time

from app.db.engine import SessionLocal
from app.db.models import Approval
from app.intent.classifier import classify_intent
from app.intent.clarification import make_clarification
from app.intent.intent_tree import extract_amount, extract_order_id, extract_sku
from app.memory import store
from app.memory.short_term import get_recent
from app.models.llm_router import get_fast_llm, get_main_llm, record_failure, record_success
from app.tools import mcp_client
from app.tools.registry import ACTION_TOOLS  # noqa: F401 (语义参考)

DEFAULT_SKU = "NX-AIR-FRYER-001"
_ROLE_MAP = {"system": "system", "user": "human", "assistant": "ai", "tool": "human"}


def _to_lc(messages: list[dict]) -> list[tuple[str, str]]:
    return [(_ROLE_MAP.get(m["role"], "human"), m["content"]) for m in messages]


# ---------- 1. load_memory ----------
def load_memory(state: dict) -> dict:
    sid = state.get("session_id")
    history, summary = [], None
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
        "结合对话历史, 把用户最新问题改写成独立完整、可直接检索的问题。只输出改写结果。\n"
        f"历史:\n{convo}\n最新问题: {q}\n改写:"
    )
    try:
        resp = get_fast_llm().invoke(prompt)
        return {"rewritten_query": (getattr(resp, "content", "") or "").strip() or q}
    except Exception:  # noqa: BLE001
        return {"rewritten_query": q}


# ---------- 3. classify_intent ----------
def classify_intent_node(state: dict) -> dict:
    q = state.get("rewritten_query") or state["question"]
    intent = classify_intent(q, state.get("history"))
    return {
        "intent": intent,
        "sku": extract_sku(state["question"]) or extract_sku(q),
        "order_id": extract_order_id(state["question"]),
        "amount": extract_amount(state["question"]),
    }


# ---------- 4. plan_tasks ----------
def plan_tasks(state: dict) -> dict:
    intent = state.get("intent")
    q = state.get("rewritten_query") or state["question"]
    sku = state.get("sku") or DEFAULT_SKU
    plan: list[dict] = []

    if intent == "anomaly_detection":
        plan = [
            {"tool": "query_sales_data", "args": {"sku": sku, "days": 7}},
            {"tool": "query_returns", "args": {"sku": sku, "days": 30}},
            {"tool": "query_inventory", "args": {"sku": sku}},
            {"tool": "query_support_tickets", "args": {"sku": sku, "days": 30}},
            {"tool": "retrieve_policy", "args": {"query": "退货率 库存安全线 暂停广告 政策"}},
        ]
    elif intent == "data_analysis":
        ql = q.lower()
        if "退货" in q or "returns" in ql:
            plan.append({"tool": "query_returns", "args": {"sku": sku, "days": 30}})
        if "销量" in q or "sales" in ql:
            plan.append({"tool": "query_sales_data", "args": {"sku": sku, "days": 7}})
        if "库存" in q or "缺货" in q or "断货" in q or "inventory" in ql or "stock" in ql:
            plan.append({"tool": "query_inventory", "args": {"sku": sku}})
        if "工单" in q:
            plan.append({"tool": "query_support_tickets", "args": {"sku": sku, "days": 30}})
        if not plan:
            plan = [
                {"tool": "query_sales_data", "args": {"sku": sku, "days": 7}},
                {"tool": "query_returns", "args": {"sku": sku, "days": 30}},
                {"tool": "query_inventory", "args": {"sku": sku}},
            ]
    elif intent == "refund_decision":
        plan = [
            {"tool": "evaluate_refund", "args": {
                "order_id": state.get("order_id") or 0,
                "amount": state.get("amount") or 0.0,
                "reason": state["question"],
            }},
            {"tool": "retrieve_policy", "args": {"query": "退款政策 金额阈值 审批 质量问题"}},
        ]
    elif intent == "knowledge_qa":
        plan = [{"tool": "retrieve_policy", "args": {"query": q}}]
    # chitchat / clarification: 空 plan
    return {"plan": plan}


# ---------- route ----------
# (router.py 提供 route_by_intent)


# ---------- 5. parallel_tool_calls ----------
def parallel_tool_calls(state: dict) -> dict:
    plan = state.get("plan") or []
    if not plan:
        return {"tool_results": [], "citations": [], "parallel_ms": 0}

    async def run_all():
        return await asyncio.gather(*[mcp_client.call_async(p["tool"], p.get("args", {})) for p in plan])

    t0 = time.monotonic()
    results = asyncio.run(run_all())
    parallel_ms = int((time.monotonic() - t0) * 1000)

    tool_results = [{"tool": p["tool"], "args": p.get("args", {}), "result": r}
                    for p, r in zip(plan, results)]
    citations = []
    for tr in tool_results:
        if tr["tool"] == "retrieve_policy" and isinstance(tr["result"], dict):
            citations = tr["result"].get("citations", [])
    return {"tool_results": tool_results, "citations": citations, "parallel_ms": parallel_ms}


# ---------- 6. validate_result ----------
def validate_result(state: dict) -> dict:
    res = {tr["tool"]: tr["result"] for tr in state.get("tool_results", [])}
    risk: list[str] = []
    ret = res.get("query_returns") or {}
    if ret.get("return_rate_pct", 0) >= 10:
        risk.append(f"退货率 {ret['return_rate_pct']}% 超过 10% 阈值")
    inv = res.get("query_inventory") or {}
    if inv.get("below_safety"):
        risk.append(f"库存 {inv.get('stock')} 低于安全线 {inv.get('safety_stock')}")
    sales = res.get("query_sales_data") or {}
    if sales.get("pct_change", 0) <= -20:
        risk.append(f"销量下降 {sales.get('pct_change')}%")
    tk = res.get("query_support_tickets") or {}
    if tk.get("count", 0) >= 10:
        risk.append(f"客诉 {tk['count']} 起, 集中在「{tk.get('top_subject')}」")
    return {"risk": risk, "high_risk": len(risk) >= 2}


# ---------- 7. human_approval_if_needed ----------
def human_approval_if_needed(state: dict) -> dict:
    intent = state.get("intent")
    sku = state.get("sku") or DEFAULT_SKU
    res = {tr["tool"]: tr["result"] for tr in state.get("tool_results", [])}
    auto: list[dict] = []
    approvals: list[dict] = []

    if intent == "anomaly_detection" and state.get("high_risk"):
        risk_text = "; ".join(state.get("risk", []))
        auto.append({"tool": "create_ops_ticket", "args": {
            "title": f"质量检查: {sku}", "sku": sku, "severity": "high",
            "body": f"高风险商品自动工单。风险: {risk_text}"}})
        auto.append({"tool": "send_slack_message", "args": {
            "channel": "#ops-alerts",
            "text": f"⚠️ 高风险商品 {sku}: {risk_text}。已建质量检查工单, 建议暂停广告并联系供应商。"}})
        # 暂停广告 = 高风险动作 → 需审批
        approvals.append({"action_type": "pause_campaign", "title": f"暂停 {sku} 广告投放",
                          "payload": {"sku": sku}})
    elif intent == "refund_decision":
        ev = res.get("evaluate_refund") or {}
        if ev.get("found"):
            payload = {"order_id": ev.get("order_id"), "amount": ev.get("amount"),
                       "reason": state["question"]}
            if ev.get("needs_approval"):
                approvals.append({"action_type": "refund", "title":
                                  f"退款审批: 订单 {ev.get('order_id')} ${ev.get('amount')}",
                                  "payload": payload})
            elif ev.get("eligible"):
                auto.append({"tool": "approve_refund_mock", "args": payload})

    # 落库 pending approvals
    pending = []
    if approvals:
        db = SessionLocal()
        try:
            for a in approvals:
                row = Approval(session_id=state.get("session_id"), trace_id=state.get("trace_id"),
                               action_type=a["action_type"], title=a["title"], payload=a["payload"],
                               status="pending")
                db.add(row)
                db.flush()
                pending.append({"id": row.id, "action_type": row.action_type, "title": row.title})
            db.commit()
        finally:
            db.close()
    return {"auto_actions": auto, "pending_approvals": pending}


# ---------- 8. execute_action ----------
def execute_action(state: dict) -> dict:
    executed = []
    for act in state.get("auto_actions") or []:
        result = mcp_client.call(act["tool"], act.get("args", {}))
        executed.append({"tool": act["tool"], "args": act.get("args", {}), "result": result})
    return {"executed_actions": executed}


# ---------- 9. final_response ----------
def final_response(state: dict) -> dict:
    intent = state.get("intent", "knowledge_qa")
    system = state.get("persona_system") or "你是 Nexora 电商运营助手。"
    q = state["question"]

    if intent == "chitchat":
        messages = [("system", system), *_to_lc(state.get("history") or []), ("human", q)]
    else:
        lines = []
        for tr in state.get("tool_results", []):
            lines.append(f"- {tr['tool']}: {tr['result']}")
        risk = state.get("risk") or []
        executed = state.get("executed_actions") or []
        pending = state.get("pending_approvals") or []
        ctx = (
            "工具结果:\n" + "\n".join(lines) + "\n\n"
            f"风险标记: {risk}\n"
            f"已执行动作: {[e['tool'] + ':' + str(e['result']) for e in executed]}\n"
            f"待人工审批: {[p['title'] for p in pending]}\n"
        )
        user = (
            f"{ctx}\n基于以上为运营人员用中文给出结论: 发现的问题、已采取的动作、待审批事项与建议。"
            "若涉及政策请用 [n] 标注引用编号。"
        )
        messages = [("system", system), ("human", user)]

    parts = []
    try:
        for chunk in get_main_llm(streaming=True).stream(messages):
            parts.append(getattr(chunk, "content", "") or "")
        record_success()
    except Exception as exc:  # noqa: BLE001
        record_failure()
        parts.append(f"生成失败: {exc}")
    return {"answer": "".join(parts)}


# ---------- clarify ----------
def clarify(state: dict) -> dict:
    text = make_clarification(state["question"])
    return {"clarification": text, "answer": text}


# ---------- save_memory ----------
def save_memory(state: dict) -> dict:
    sid = state.get("session_id")
    if sid:
        from app.memory.short_term import append_turn

        append_turn(sid, "user", state["question"])
        append_turn(sid, "assistant", state.get("answer", ""))
    return {}
