"""Order Agent: a ReAct tool-calling loop that fetches order data and writes the reply."""

from typing import Dict, List, Tuple

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from ..config import settings
from ..llm import get_agent_llm
from ..prompts import ORDER_AGENT_SYSTEM_PROMPT, ORDER_AGENT_USER_TEMPLATE
from ..tools import TOOLS, TOOLS_BY_NAME
from ..utils import strip_final_answer_prefix


def _format_history(history: List[Dict[str, str]]) -> str:
    if not history:
        return ""
    lines = "\n".join(f"User: {h['user']}\nAssistant: {h['assistant']}" for h in history)
    return f"Previous conversation:\n{lines}\n\n"


def run_order_agent(query: str, order_id: str,
                    history: List[Dict[str, str]]) -> Tuple[str, str]:
    """Run the ReAct loop. Returns (order_context, final_response)."""
    llm_with_tools = get_agent_llm().bind_tools(TOOLS)

    user_content = ORDER_AGENT_USER_TEMPLATE.format(
        history_block=_format_history(history),
        query=query,
        order_id=order_id,
        today=settings.today,
    )
    messages = [SystemMessage(content=ORDER_AGENT_SYSTEM_PROMPT),
                HumanMessage(content=user_content)]

    order_context = ""
    ai_msg = None
    for _ in range(settings.max_tool_iterations):
        ai_msg = llm_with_tools.invoke(messages)
        messages.append(ai_msg)

        # No tool calls means the agent produced its Final Answer.
        if not getattr(ai_msg, "tool_calls", None):
            break

        # Observation step: execute each requested tool call.
        for tc in ai_msg.tool_calls:
            tool = TOOLS_BY_NAME.get(tc["name"])
            result = tool.invoke(tc["args"]) if tool else f"Unknown tool: {tc['name']}"
            if tc["name"] == "fetch_order_details":
                order_context = result
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    final_response = strip_final_answer_prefix(ai_msg.content if ai_msg else "")
    return order_context, final_response
