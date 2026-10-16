"""LangGraph workflow for a single conversation turn.

    START -> intent_classifier --(process)--> order_agent -> evaluate --(pass)--> safety_check
                 |                                ^            |                    |
                 |                                +--(retry)---+                (safe)
                 +--(escalate/exit/off-topic)--> exit_node -> END                   v
                                                                         memory_save -> conv_safety_check -> END

The outer chat loop (CLI or Streamlit) feeds one user message per graph run,
which replaces the notebook's blocking input() node.
"""

from langgraph.graph import END, START, StateGraph

from .nodes import (
    conversational_guard_node,
    evaluation_node,
    exit_node,
    guard_node,
    guard_router,
    intent_node,
    intent_router,
    memory_node,
    order_agent_node,
    retry_router,
)
from .state import OrderState


def debug_node(name, fn):
    """Wrap a node to print the state update it produces."""
    def wrapper(state):
        print(f"\n===== RUNNING NODE: {name} =====")
        result = fn(state)
        for k, v in result.items():
            print(f"  {k}: {v}")
        print("================================")
        return result
    return wrapper


def build_graph(debug: bool = False):
    wrap = (lambda name, fn: debug_node(name, fn)) if debug else (lambda name, fn: fn)

    graph = StateGraph(OrderState)
    graph.add_node("intent_classifier", wrap("intent_classifier", intent_node))
    graph.add_node("order_agent",       wrap("order_agent",       order_agent_node))
    graph.add_node("evaluate",          wrap("evaluate",          evaluation_node))
    graph.add_node("safety_check",      wrap("safety_check",      guard_node))
    graph.add_node("memory_save",       wrap("memory_save",       memory_node))
    graph.add_node("conv_safety_check", wrap("conv_safety_check", conversational_guard_node))
    graph.add_node("exit_node",         wrap("exit_node",         exit_node))

    graph.add_edge(START, "intent_classifier")
    graph.add_conditional_edges(
        "intent_classifier", intent_router,
        {"order_agent": "order_agent", "exit_node": "exit_node"},
    )
    graph.add_edge("order_agent", "evaluate")
    graph.add_conditional_edges(
        "evaluate", retry_router,
        {"order_agent": "order_agent", "safety_check": "safety_check", "end": END},
    )
    graph.add_conditional_edges(
        "safety_check", guard_router,
        {"memory_save": "memory_save", "end": END},
    )
    graph.add_edge("memory_save", "conv_safety_check")
    graph.add_edge("conv_safety_check", END)
    graph.add_edge("exit_node", END)

    return graph.compile()
