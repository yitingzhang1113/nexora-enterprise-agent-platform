"""文本清洗: 压缩多余空白、去控制字符。"""
from __future__ import annotations

import re

_WS = re.compile(r"[ \t]+")
_NL = re.compile(r"\n{3,}")


def clean(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\x00", "")
    text = _WS.sub(" ", text)
    text = _NL.sub("\n\n", text)
    return text.strip()
