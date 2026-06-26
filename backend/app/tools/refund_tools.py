"""退款类 MCP 工具: 评估退款资格 / 执行退款 (mock)。"""
from __future__ import annotations

from app.db.engine import SessionLocal
from app.db.models import Order, RefundRequest

APPROVAL_THRESHOLD = 200.0
DEFECT_WORDS = ["broken", "defective", "damaged", "故障", "损坏", "把手", "handle"]

EVAL_SCHEMA = {
    "name": "evaluate_refund",
    "description": "根据订单与退款政策评估某笔退款是否可退、是否需要人工审批。",
    "parameters": {
        "type": "object",
        "properties": {
            "order_id": {"type": "integer"},
            "amount": {"type": "number"},
            "reason": {"type": "string"},
        },
        "required": ["order_id"],
    },
}


def evaluate_refund(order_id: int = 0, amount: float = 0.0, reason: str = "", **_) -> dict:
    db = SessionLocal()
    try:
        order = db.get(Order, int(order_id)) if order_id else None
        if not order:
            return {"order_id": order_id, "found": False, "eligible": False,
                    "needs_approval": False, "policy_reason": "订单不存在"}
        amt = float(amount) or float(order.total)
        is_defect = any(w in (reason or "").lower() for w in DEFECT_WORDS)
        eligible = is_defect or amt <= order.total
        needs_approval = amt > APPROVAL_THRESHOLD
        policy_reason = (
            f"金额 ${amt:.2f} {'>' if needs_approval else '<='} ${APPROVAL_THRESHOLD:.0f} 阈值; "
            f"{'质量问题可退款' if is_defect else '常规退款'}; "
            f"{'需经理审批' if needs_approval else '可直接处理'}"
        )
        return {
            "order_id": order_id, "found": True, "amount": amt, "order_total": order.total,
            "eligible": eligible, "needs_approval": needs_approval, "policy_reason": policy_reason,
        }
    finally:
        db.close()


APPROVE_SCHEMA = {
    "name": "approve_refund_mock",
    "description": "执行退款 (mock): 记录退款并标记完成。",
    "parameters": {
        "type": "object",
        "properties": {
            "order_id": {"type": "integer"},
            "amount": {"type": "number"},
            "reason": {"type": "string"},
        },
        "required": ["order_id"],
    },
}


def approve_refund_mock(order_id: int = 0, amount: float = 0.0, reason: str = "", **_) -> dict:
    db = SessionLocal()
    try:
        r = RefundRequest(order_id=int(order_id), amount=float(amount), reason=reason, status="refunded")
        db.add(r)
        db.commit()
        db.refresh(r)
        return {"order_id": order_id, "refund_id": r.id, "status": "refunded", "amount": r.amount}
    finally:
        db.close()
