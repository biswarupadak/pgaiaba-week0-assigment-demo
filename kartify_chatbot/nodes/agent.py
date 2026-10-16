"""Graph nodes that run the Order Agent and save the turn to memory."""

from ..agents import run_order_agent
from ..state import OrderState


def order_agent_node(state: OrderState) -> dict:
    order_context, final_response = run_order_agent(
        query=state["query"],
        order_id=state["order_id"],
        history=state["history"],
    )
    return {
        "order_context": order_context,
        "final_response": final_response,
        "attempts": state["attempts"] + 1,
    }


def memory_node(state: OrderState) -> dict:
    """Append this turn to the conversation history."""
    turn = {"user": state["query"], "assistant": state["final_response"]}
    return {"history": state["history"] + [turn]}
