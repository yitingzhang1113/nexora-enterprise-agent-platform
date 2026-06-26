"""动作类 MCP 工具 (有副作用): 建工单 / 发 Slack / 暂停广告。"""
from __future__ import annotations

import httpx
from sqlalchemy import select, update

from app.config import settings
from app.db.engine import SessionLocal
from app.db.models import Campaign, OpsTicket, SlackMessage

# ---------- create_ops_ticket ----------
CREATE_TICKET_SCHEMA = {
    "name": "create_ops_ticket",
    "description": "创建一个运营工单 (如质量检查、补货)。",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "sku": {"type": "string"},
            "severity": {"type": "string", "enum": ["low", "medium", "high"]},
            "body": {"type": "string"},
        },
        "required": ["title"],
    },
}


def create_ops_ticket(title: str = "", sku: str = "", severity: str = "medium", body: str = "", **_) -> dict:
    db = SessionLocal()
    try:
        t = OpsTicket(title=title, sku=sku or None, severity=severity, body=body, status="open")
        db.add(t)
        db.commit()
        db.refresh(t)
        return {"ticket_id": t.id, "title": t.title, "severity": t.severity, "status": t.status}
    finally:
        db.close()


# ---------- send_slack_message ----------
SLACK_SCHEMA = {
    "name": "send_slack_message",
    "description": "向运营 Slack 频道发送通知消息。",
    "parameters": {
        "type": "object",
        "properties": {
            "channel": {"type": "string", "description": "如 #ops-alerts"},
            "text": {"type": "string"},
        },
        "required": ["text"],
    },
}


def send_slack_message(channel: str = "#ops-alerts", text: str = "", **_) -> dict:
    sent_real = False
    if settings.slack_webhook_url:
        try:
            httpx.post(settings.slack_webhook_url, json={"text": f"[{channel}] {text}"}, timeout=10)
            sent_real = True
        except Exception:  # noqa: BLE001
            sent_real = False
    db = SessionLocal()
    try:
        m = SlackMessage(channel=channel, text=text, sent_real=sent_real)
        db.add(m)
        db.commit()
        return {"ok": True, "channel": channel, "sent_real": sent_real}
    finally:
        db.close()


# ---------- pause_campaign ----------
PAUSE_SCHEMA = {
    "name": "pause_campaign",
    "description": "暂停某 SKU 的所有在投广告活动 (高风险操作)。",
    "parameters": {
        "type": "object",
        "properties": {"sku": {"type": "string"}},
        "required": ["sku"],
    },
}


def pause_campaign(sku: str = "", **_) -> dict:
    db = SessionLocal()
    try:
        rows = db.execute(
            select(Campaign).where(Campaign.sku == sku, Campaign.status == "active")
        ).scalars().all()
        names = [c.name for c in rows]
        if rows:
            db.execute(
                update(Campaign).where(Campaign.sku == sku, Campaign.status == "active").values(status="paused")
            )
            db.commit()
        return {"sku": sku, "paused_campaigns": names, "count": len(names)}
    finally:
        db.close()
