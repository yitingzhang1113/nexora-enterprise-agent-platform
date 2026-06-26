"""销售数据工具 (mock)。"""
from __future__ import annotations

SCHEMA = {
    "name": "query_sales",
    "description": "查询某时间段/地区的销售数据。",
    "parameters": {
        "type": "object",
        "properties": {
            "period": {"type": "string", "description": "如 2026Q2 / 6月"},
            "region": {"type": "string", "description": "地区, 可选"},
        },
        "required": ["period"],
    },
}


def run(period: str = "", region: str = "", **_) -> str:
    region_part = f"{region}地区 " if region else "全区 "
    return (
        f"{region_part}{period or '本期'} 销售额: ¥1,280,000, 同比 +12.4%, "
        f"订单数 3,420 (示例数据)"
    )
