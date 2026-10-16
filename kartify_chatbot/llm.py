"""Chat model factories. Models are created lazily so imports never need an API key."""

from functools import lru_cache

from langchain_openai import ChatOpenAI

from .config import load_credentials, settings


@lru_cache(maxsize=1)
def get_agent_llm() -> ChatOpenAI:
    """LLM used by the Order Agent (tool calling + answer generation)."""
    load_credentials()
    return ChatOpenAI(model=settings.agent_model)


@lru_cache(maxsize=1)
def get_judge_llm() -> ChatOpenAI:
    """Stronger LLM used for evaluation, intent classification and guardrails."""
    load_credentials()
    return ChatOpenAI(model=settings.judge_model)
