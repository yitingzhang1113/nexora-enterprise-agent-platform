"""LangGraph 工作流装配。

START → load_memory → rewrite_query → classify_intent → route:
  knowledge_qa: retrieve_docs → rerank → build_prompt → generate → save_memory → END
  tool_call:    call_tools → build_prompt → generate → save_memory → END
  chitchat:     build_prompt → generate → save_memory → END
  clarification: clarify → END
"""
from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    build_prompt,
    call_tools,
    clarify,
    classify_intent_node,
    generate,
    load_memory,
    rerank_node,
    retrieve_docs,
    rewrite_query,
    save_memory,
)
from app.graph.router import route_by_intent
from app.graph.state import AgentState


@lru_cache
def get_workflow():
    g = StateGraph(AgentState)

    g.add_node("load_memory", load_memory)
    g.add_node("rewrite_query", rewrite_query)
    g.add_node("classify_intent", classify_intent_node)
    g.add_node("retrieve_docs", retrieve_docs)
    g.add_node("rerank", rerank_node)
    g.add_node("call_tools", call_tools)
    g.add_node("clarify", clarify)
    g.add_node("build_prompt", build_prompt)
    g.add_node("generate", generate)
    g.add_node("save_memory", save_memory)

    g.add_edge(START, "load_memory")
    g.add_edge("load_memory", "rewrite_query")
    g.add_edge("rewrite_query", "classify_intent")

    g.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "retrieve_docs": "retrieve_docs",
            "call_tools": "call_tools",
            "clarify": "clarify",
            "build_prompt": "build_prompt",
        },
    )

    g.add_edge("retrieve_docs", "rerank")
    g.add_edge("rerank", "build_prompt")
    g.add_edge("call_tools", "build_prompt")
    g.add_edge("build_prompt", "generate")
    g.add_edge("generate", "save_memory")
    g.add_edge("save_memory", END)
    g.add_edge("clarify", END)

    return g.compile()
