"""澄清: 当意图为 clarification 时, 生成一个澄清问题。"""
from __future__ import annotations

_FALLBACK = "能否请你提供更多细节？比如你具体想了解什么、涉及哪个产品或时间范围？"

_PROMPT = (
    "用户的问题比较模糊, 请用一句话礼貌地向用户提出一个澄清问题, 帮助你更好地回答。"
    "只输出这句澄清问题本身。\n用户问题: {q}\n澄清问题:"
)


def make_clarification(query: str) -> str:
    try:
        from app.models.llm_router import get_fast_llm

        resp = get_fast_llm().invoke(_PROMPT.format(q=query))
        text = (getattr(resp, "content", "") or "").strip()
        return text or _FALLBACK
    except Exception:  # noqa: BLE001
        return _FALLBACK
