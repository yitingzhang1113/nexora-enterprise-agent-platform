"""天气工具 (mock)。"""
from __future__ import annotations

SCHEMA = {
    "name": "get_weather",
    "description": "查询某城市的当前天气。",
    "parameters": {
        "type": "object",
        "properties": {"city": {"type": "string", "description": "城市名"}},
        "required": ["city"],
    },
}

_FAKE = {
    "北京": "晴, 26°C, 西北风 3 级",
    "上海": "多云, 28°C, 东南风 2 级",
    "深圳": "雷阵雨, 30°C, 湿度 80%",
}


def run(city: str = "", **_) -> str:
    city = (city or "").strip()
    weather = _FAKE.get(city, "晴转多云, 25°C (示例数据)")
    return f"{city or '该地区'} 当前天气: {weather}"
