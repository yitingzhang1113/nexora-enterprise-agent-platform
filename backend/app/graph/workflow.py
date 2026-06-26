"""LangGraph 工作流 (v4 Ops Agent)。

load_memory → rewrite_query → classify_intent → plan_tasks → route
  ├ clarification → clarify → END
  └ 其余 → parallel_tool_calls → validate_result → human_approval_if_needed
           → execute_action → final_response → save_memory → END
"""
from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    clarify,
    classify_intent_node,
    execute_action,
    final_response,
    human_approval_if_needed,
    load_memory,
    parallel_tool_calls,
    plan_tasks,
    rewrite_query,
    save_memory,
    validate_result,
)
from app.graph.router import route_by_intent
from app.graph.state import AgentState


@lru_cache
def get_workflow():
    g = StateGraph(AgentState)

    g.add_node("load_memory", load_memory)
    g.add_node("rewrite_query", rewrite_query)
    g.add_node("classify_intent", classify_intent_node)
    g.add_node("plan_tasks", plan_tasks)
    g.add_node("parallel_tool_calls", parallel_tool_calls)
    g.add_node("validate_result", validate_result)
    g.add_node("human_approval_if_needed", human_approval_if_needed)
    g.add_node("execute_action", execute_action)
    g.add_node("final_response", final_response)
    g.add_node("clarify", clarify)
    g.add_node("save_memory", save_memory)

    g.add_edge(START, "load_memory")
    g.add_edge("load_memory", "rewrite_query")
    g.add_edge("rewrite_query", "classify_intent")
    g.add_edge("classify_intent", "plan_tasks")
    g.add_conditional_edges(
        "plan_tasks",
        route_by_intent,
        {"clarify": "clarify", "parallel_tool_calls": "parallel_tool_calls"},
    )
    g.add_edge("parallel_tool_calls", "validate_result")
    g.add_edge("validate_result", "human_approval_if_needed")
    g.add_edge("human_approval_if_needed", "execute_action")
    g.add_edge("execute_action", "final_response")
    g.add_edge("final_response", "save_memory")
    g.add_edge("save_memory", END)
    g.add_edge("clarify", END)

    return g.compile()
