"""对话摘要 (LLM): 历史过长时滚动摘要, 控制上下文长度。"""
from __future__ import annotations

SUMMARIZE_THRESHOLD = 10  # 历史消息超过此数才摘要

_PROMPT = (
    "请把下面的多轮对话压缩成一段简洁的中文摘要, 保留关键事实、用户偏好与未决问题, "
    "不超过 150 字。\n\n对话:\n{conv}\n\n摘要:"
)


def summarize(history: list[dict], prev_summary: str | None = None) -> str | None:
    if len(history) < SUMMARIZE_THRESHOLD:
        return None
    conv = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    if prev_summary:
        conv = f"(已有摘要: {prev_summary})\n{conv}"
    try:
        from app.models.llm_router import get_fast_llm

        resp = get_fast_llm().invoke(_PROMPT.format(conv=conv))
        return (getattr(resp, "content", "") or "").strip() or None
    except Exception:  # noqa: BLE001
        return None
