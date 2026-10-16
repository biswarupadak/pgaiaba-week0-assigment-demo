"""Three guardrail layers: input (intent), output (per reply) and conversation level."""

from langchain_core.messages import HumanMessage

from ..llm import get_judge_llm
from ..prompts import CONVERSATION_GUARD_PROMPT, INTENT_PROMPT, OUTPUT_GUARD_PROMPT
from ..state import OrderState
from ..utils import normalize_intent, normalize_verdict
from .messages import ESCALATION_REPLY, EXIT_REPLY, HANDOFF_REPLY, OUT_OF_SCOPE_REPLY

INTENT_ESCALATE, INTENT_EXIT, INTENT_PROCESS, INTENT_OUT_OF_SCOPE = "0", "1", "2", "3"


def _ask_judge(prompt: str) -> str:
    return get_judge_llm().invoke([HumanMessage(content=prompt)]).content


# ---- Input guardrail ------------------------------------------------------

def intent_node(state: OrderState) -> dict:
    raw = _ask_judge(INTENT_PROMPT.format(query=state["query"]))
    return {"intent": normalize_intent(raw)}


def intent_router(state: OrderState) -> str:
    return "order_agent" if state["intent"] == INTENT_PROCESS else "exit_node"


def exit_node(state: OrderState) -> dict:
    """Reply for queries the agent should not process."""
    if state["intent"] == INTENT_ESCALATE:
        return {"final_response": ESCALATION_REPLY, "ended": True}
    if state["intent"] == INTENT_EXIT:
        return {"final_response": EXIT_REPLY, "ended": True}
    # Out-of-scope / suspicious input: refuse politely but keep the chat open.
    return {"final_response": OUT_OF_SCOPE_REPLY}


# ---- Output guardrail -----------------------------------------------------

def guard_node(state: OrderState) -> dict:
    verdict = normalize_verdict(
        _ask_judge(OUTPUT_GUARD_PROMPT.format(response=state["final_response"])))
    update = {"guard_result": verdict}
    if verdict == "BLOCK":
        update.update(final_response=HANDOFF_REPLY, ended=True)
    return update


def guard_router(state: OrderState) -> str:
    return "end" if state["guard_result"] == "BLOCK" else "memory_save"


# ---- Conversation-level guardrail ----------------------------------------

def conversational_guard_node(state: OrderState) -> dict:
    conversation = "\n".join(
        f"User: {h['user']}\nAssistant: {h['assistant']}" for h in state["history"])
    verdict = normalize_verdict(
        _ask_judge(CONVERSATION_GUARD_PROMPT.format(conversation=conversation)))
    update = {"conv_guard_result": verdict}
    if verdict == "BLOCK":
        update.update(final_response=HANDOFF_REPLY, ended=True)
    return update
