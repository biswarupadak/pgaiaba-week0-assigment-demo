"""Shared LangGraph state that flows between all nodes."""

from typing import Dict, List, TypedDict


class OrderState(TypedDict):
    cust_id: str
    order_id: str
    query: str
    order_context: str            # raw tool output the agent saw (used for evaluation)
    final_response: str
    history: List[Dict[str, str]] # [{"user": ..., "assistant": ...}, ...]
    intent: str                   # "0" escalate, "1" exit, "2" process, "3" out-of-scope
    evaluation: Dict[str, float]  # {"groundedness": x, "precision": y}
    attempts: int                 # number of Order Agent runs this turn
    guard_result: str             # output guardrail: SAFE / BLOCK
    conv_guard_result: str        # conversation guardrail: SAFE / BLOCK
    ended: bool                   # True when the conversation should stop


def new_turn_state(cust_id: str, order_id: str, query: str,
                   history: List[Dict[str, str]]) -> OrderState:
    """Build a fresh state for one user turn."""
    return {
        "cust_id": cust_id,
        "order_id": order_id,
        "query": query,
        "order_context": "",
        "final_response": "",
        "history": list(history),
        "intent": "",
        "evaluation": {},
        "attempts": 0,
        "guard_result": "",
        "conv_guard_result": "",
        "ended": False,
    }
