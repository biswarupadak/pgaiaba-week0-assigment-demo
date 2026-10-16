"""LLM-as-judge evaluation of the agent reply (groundedness + precision) with retry routing."""

from langchain_core.messages import HumanMessage

from ..config import settings
from ..llm import get_judge_llm
from ..prompts import EVALUATION_PROMPT
from ..state import OrderState
from ..utils import extract_json_from_llm
from .messages import HANDOFF_REPLY


def evaluate_response(context: str, query: str, response: str) -> dict:
    """Score a reply. Any failure to parse scores 0.0 so the reply is retried."""
    prompt = EVALUATION_PROMPT.format(context=context, query=query, response=response)
    try:
        raw = get_judge_llm().invoke([HumanMessage(content=prompt)]).content
        scores = extract_json_from_llm(raw)
        return {
            "groundedness": float(scores.get("groundedness", 0.0)),
            "precision": float(scores.get("precision", 0.0)),
        }
    except Exception:
        return {"groundedness": 0.0, "precision": 0.0}


def passes(evaluation: dict) -> bool:
    return (evaluation.get("groundedness", 0.0) >= settings.eval_threshold
            and evaluation.get("precision", 0.0) >= settings.eval_threshold)


def evaluation_node(state: OrderState) -> dict:
    evaluation = evaluate_response(state["order_context"], state["query"],
                                   state["final_response"])
    update = {"evaluation": evaluation}
    # Out of retries: hand off to a human rather than send a low-quality reply.
    if not passes(evaluation) and state["attempts"] >= settings.max_agent_attempts:
        update.update(final_response=HANDOFF_REPLY, ended=True)
    return update


def retry_router(state: OrderState) -> str:
    if state["ended"]:
        return "end"
    if not passes(state["evaluation"]):
        return "order_agent"
    return "safety_check"
