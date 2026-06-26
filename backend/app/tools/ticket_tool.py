"""工单工具 (mock)。"""
from __future__ import annotations

SCHEMA = {
    "name": "query_ticket",
    "description": "查询工单状态, 或创建一个新工单。",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["query", "create"]},
            "ticket_id": {"type": "string", "description": "工单号 (query 时)"},
            "title": {"type": "string", "description": "工单标题 (create 时)"},
        },
        "required": ["action"],
    },
}


def run(action: str = "query", ticket_id: str = "", title: str = "", **_) -> str:
    if action == "create":
        return f"已创建工单 #T-2026-{abs(hash(title)) % 10000:04d}: {title or '未命名'} (状态: open)"
    return f"工单 {ticket_id or 'T-2026-0001'} 状态: 处理中, 预计 1 个工作日内完成 (示例数据)"
