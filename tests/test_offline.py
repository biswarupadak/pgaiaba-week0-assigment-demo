"""Offline tests: database, tool, parsing helpers, and the full graph with fake LLMs."""

import pytest
from langchain_core.messages import AIMessage

from kartify_chatbot import ChatSession, database
from kartify_chatbot.agents import order_agent
from kartify_chatbot.nodes import evaluation, guardrails
from kartify_chatbot.nodes.messages import EXIT_REPLY, HANDOFF_REPLY, OUT_OF_SCOPE_REPLY
from kartify_chatbot.tools import fetch_order_details
from kartify_chatbot.utils import (
    extract_json_from_llm, normalize_intent, normalize_verdict, strip_final_answer_prefix)


# ---- Database & tool -------------------------------------------------------

def test_get_order_found():
    df = database.get_order("O40327")
    assert df.iloc[0]["customer_id"] == "C1010"


def test_customer_orders_and_ownership():
    assert "O48601" in set(database.get_customer_orders("C1011")["order_id"])
    assert database.order_belongs_to_customer("O48601", "C1011")
    assert not database.order_belongs_to_customer("O40327", "C1011")


def test_tool_rejects_bad_id_and_handles_missing():
    assert "Invalid order ID" in fetch_order_details.invoke({"order_id": "1; DROP TABLE orders"})
    assert "No order found" in fetch_order_details.invoke({"order_id": "O99999999"})
    assert "TRK552659" in fetch_order_details.invoke({"order_id": "O40327"})


# ---- Parsing helpers -------------------------------------------------------

@pytest.mark.parametrize("text", [
    '```json\n{"groundedness": 0.9, "precision": 0.8}\n```',
    'Scores: {"groundedness": 0.9, "precision": 0.8}',
])
def test_extract_json(text):
    assert extract_json_from_llm(text) == {"groundedness": 0.9, "precision": 0.8}


def test_strip_final_answer_prefix():
    assert strip_final_answer_prefix("Thought: x\nFinal Answer: Delivered.") == "Delivered."
    assert strip_final_answer_prefix("Delivered.") == "Delivered."


def test_normalizers():
    assert normalize_intent(" 2\n") == "2"
    assert normalize_intent("unclear") == "3"
    assert normalize_verdict("SAFE.") == "SAFE"
    assert normalize_verdict("BLOCK") == "BLOCK"
    assert normalize_verdict("???") == "BLOCK"   # fail closed


# ---- Full graph with fake LLMs ---------------------------------------------

class FakeAgentLLM:
    """Calls the tool once, then returns a final answer."""
    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        if not any(m.type == "tool" for m in messages):
            return AIMessage(content="", tool_calls=[
                {"name": "fetch_order_details", "args": {"order_id": "O40327"}, "id": "c1"}])
        return AIMessage(content="Thought: done\nFinal Answer: Your order was delivered on 14-07.")


class FakeJudgeLLM:
    """Answers each judge prompt type with a scripted reply."""
    def __init__(self, intent="2", scores='{"groundedness": 0.9, "precision": 0.9}',
                 guard="SAFE", conv_guard="SAFE"):
        self.intent, self.scores, self.guard, self.conv_guard = intent, scores, guard, conv_guard

    def invoke(self, messages):
        prompt = messages[0].content
        if "intent classifier" in prompt:
            return AIMessage(content=self.intent)
        if "Groundedness" in prompt:
            return AIMessage(content=self.scores)
        if "content safety" in prompt:
            return AIMessage(content=self.guard)
        return AIMessage(content=self.conv_guard)


@pytest.fixture
def fake_llms(monkeypatch):
    def install(**judge_kwargs):
        judge = FakeJudgeLLM(**judge_kwargs)
        monkeypatch.setattr(order_agent, "get_agent_llm", lambda: FakeAgentLLM())
        monkeypatch.setattr(evaluation, "get_judge_llm", lambda: judge)
        monkeypatch.setattr(guardrails, "get_judge_llm", lambda: judge)
    return install


def test_happy_path_saves_memory(fake_llms):
    fake_llms()
    session = ChatSession("C1010", "O40327")
    result = session.ask("Where is my order?")
    assert result.reply == "Your order was delivered on 14-07."
    assert not result.ended
    assert "TRK552659" in result.state["order_context"]
    assert session.memory.get() == [{"user": "Where is my order?", "assistant": result.reply}]


def test_output_guard_blocks(fake_llms):
    fake_llms(guard="BLOCK")
    session = ChatSession("C1010", "O40327")
    result = session.ask("Refund please")
    assert result.reply == HANDOFF_REPLY and result.ended
    assert session.memory.get() == []


def test_conversation_guard_blocks(fake_llms):
    fake_llms(conv_guard="BLOCK")
    result = ChatSession("C1010", "O40327").ask("Where is my order?")
    assert result.reply == HANDOFF_REPLY and result.ended


def test_low_scores_retry_then_handoff(fake_llms):
    fake_llms(scores='{"groundedness": 0.2, "precision": 0.2}')
    result = ChatSession("C1010", "O40327").ask("Where is my order?")
    assert result.state["attempts"] == 3
    assert result.reply == HANDOFF_REPLY and result.ended


def test_exit_and_out_of_scope_intents(fake_llms):
    fake_llms(intent="3")
    session = ChatSession("C1010", "O40327")
    result = session.ask("What is NLP?")
    assert result.reply == OUT_OF_SCOPE_REPLY and not result.ended

    fake_llms(intent="1")
    result = session.ask("Thanks!")
    assert result.reply == EXIT_REPLY and result.ended
