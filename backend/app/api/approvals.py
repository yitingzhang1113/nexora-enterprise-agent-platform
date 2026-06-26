"""审批队列 API: 列表 / 通过(→执行动作) / 拒绝。"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.engine import get_session
from app.db.models import Approval
from app.tools import mcp_client

router = APIRouter(prefix="/approvals", tags=["approvals"])


def _execute(approval: Approval) -> dict:
    """按 action_type 执行实际动作 + Slack 通知。"""
    a = approval.action_type
    payload = approval.payload or {}
    if a == "pause_campaign":
        result = mcp_client.call("pause_campaign", {"sku": payload.get("sku")})
    elif a == "refund":
        result = mcp_client.call("approve_refund_mock", payload)
    elif a == "create_ticket":
        result = mcp_client.call("create_ops_ticket", payload)
    else:
        result = {"error": f"未知 action_type: {a}"}
    mcp_client.call("send_slack_message", {
        "channel": "#ops-alerts",
        "text": f"✅ 审批通过并执行: {approval.title} → {result}",
    })
    return result


@router.get("")
def list_approvals(status: str | None = None, db: Session = Depends(get_session)) -> list[dict]:
    q = select(Approval).order_by(Approval.id.desc())
    if status:
        q = q.where(Approval.status == status)
    rows = db.execute(q).scalars()
    return [
        {"id": r.id, "action_type": r.action_type, "title": r.title, "payload": r.payload,
         "status": r.status, "reason": r.reason, "result": r.result,
         "created_at": r.created_at.isoformat() if r.created_at else None}
        for r in rows
    ]


@router.post("/{approval_id}/approve")
def approve(approval_id: int, db: Session = Depends(get_session)) -> dict:
    a = db.get(Approval, approval_id)
    if not a:
        raise HTTPException(status_code=404, detail="审批不存在")
    if a.status != "pending":
        return {"id": a.id, "status": a.status, "note": "已处理过"}
    result = _execute(a)
    a.status = "executed"
    a.result = result
    a.decided_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": a.id, "status": a.status, "result": result}


@router.post("/{approval_id}/reject")
def reject(approval_id: int, reason: str = "", db: Session = Depends(get_session)) -> dict:
    a = db.get(Approval, approval_id)
    if not a:
        raise HTTPException(status_code=404, detail="审批不存在")
    a.status = "rejected"
    a.reason = reason or "运营拒绝"
    a.decided_at = datetime.now(timezone.utc)
    db.commit()
    return {"id": a.id, "status": a.status}
