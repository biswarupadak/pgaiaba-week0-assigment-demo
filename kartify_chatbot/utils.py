"""Small parsing helpers for LLM output."""

import json
import re
from typing import Any


def extract_json_from_llm(text: str) -> Any:
    """Extract a JSON value from LLM output (fenced ```json block, bare object or array)."""
    for pattern in (r"```(?:json)?\s*(.*?)\s*```", r"\{.*\}", r"\[.*\]"):
        match = re.search(pattern, text, re.DOTALL)
        if match:
            candidate = match.group(1) if "```" in pattern else match.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
    return json.loads(text)


def strip_final_answer_prefix(text: str) -> str:
    """Return only the customer-facing part of a ReAct reply.

    If the model echoed its Thought/Action trace, keep what follows the last
    "Final Answer:" marker.
    """
    return re.split(r"final answer:\s*", text, flags=re.IGNORECASE)[-1].strip()


def normalize_verdict(text: str) -> str:
    """Map a guardrail LLM reply to SAFE or BLOCK (fail closed on anything unexpected)."""
    upper = text.strip().upper()
    if "BLOCK" in upper:
        return "BLOCK"
    if "SAFE" in upper:
        return "SAFE"
    return "BLOCK"


def normalize_intent(text: str) -> str:
    """Pull the first category digit 0-3 out of the classifier reply ("3" if none)."""
    match = re.search(r"[0-3]", text)
    return match.group(0) if match else "3"
