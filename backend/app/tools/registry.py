"""MCP 工具注册表 (电商运营 10 工具)。schema + executor, 记录调用计数。"""
from __future__ import annotations

from typing import Callable

from app.observability import metrics
from app.tools import action_tools as A
from app.tools import data_tools as D
from app.tools import policy_tool as P
from app.tools import refund_tools as R

# name -> (schema, executor) executor 返回 dict
_TOOLS: dict[str, tuple[dict, Callable[..., dict]]] = {
    D.SALES_SCHEMA["name"]: (D.SALES_SCHEMA, D.query_sales_data),
    D.INVENTORY_SCHEMA["name"]: (D.INVENTORY_SCHEMA, D.query_inventory),
    D.RETURNS_SCHEMA["name"]: (D.RETURNS_SCHEMA, D.query_returns),
    D.TICKETS_SCHEMA["name"]: (D.TICKETS_SCHEMA, D.query_support_tickets),
    P.POLICY_SCHEMA["name"]: (P.POLICY_SCHEMA, P.retrieve_policy),
    A.CREATE_TICKET_SCHEMA["name"]: (A.CREATE_TICKET_SCHEMA, A.create_ops_ticket),
    A.SLACK_SCHEMA["name"]: (A.SLACK_SCHEMA, A.send_slack_message),
    A.PAUSE_SCHEMA["name"]: (A.PAUSE_SCHEMA, A.pause_campaign),
    R.EVAL_SCHEMA["name"]: (R.EVAL_SCHEMA, R.evaluate_refund),
    R.APPROVE_SCHEMA["name"]: (R.APPROVE_SCHEMA, R.approve_refund_mock),
}

# 区分只读工具与有副作用 (动作) 工具
ACTION_TOOLS = {"create_ops_ticket", "send_slack_message", "pause_campaign", "approve_refund_mock"}


def list_schemas() -> list[dict]:
    return [s for s, _ in _TOOLS.values()]


def tool_names() -> list[str]:
    return list(_TOOLS.keys())


def run_local(name: str, args: dict) -> dict:
    entry = _TOOLS.get(name)
    if not entry:
        return {"error": f"未知工具: {name}"}
    metrics.incr(f"tool.{name}")
    _, fn = entry
    return fn(**(args or {}))
