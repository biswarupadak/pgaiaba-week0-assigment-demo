"""Application settings: API credentials, model names, paths and thresholds."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    db_path: Path = PROJECT_ROOT / "kartify.db"
    config_path: Path = PROJECT_ROOT / "config.json"

    # gpt-4o-mini: fast and cheap, used by the Order Agent.
    agent_model: str = "gpt-4o-mini"
    # gpt-4o: more capable, used for evaluation, intent classification and guardrails.
    judge_model: str = "gpt-4o"

    # The sample data is static, so "today" is pinned to a date that matches it.
    today: str = "25 July"

    max_tool_iterations: int = 5      # ReAct loop safety cap
    eval_threshold: float = 0.75      # min groundedness / precision to accept a reply
    max_agent_attempts: int = 3       # retries when evaluation fails


settings = Settings()


def load_credentials(config_path: Path | None = None) -> None:
    """Load OPENAI_API_KEY / OPENAI_API_BASE from config.json into the environment.

    Values already present in the environment win, so the app can also be
    configured purely through env vars (e.g. Streamlit secrets).
    """
    path = Path(config_path or settings.config_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
        if config.get("OPENAI_API_KEY"):
            os.environ.setdefault("OPENAI_API_KEY", config["OPENAI_API_KEY"])
        if config.get("OPENAI_API_BASE"):
            os.environ.setdefault("OPENAI_BASE_URL", config["OPENAI_API_BASE"])

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY not found. Create config.json (see config.example.json) "
            "or set the OPENAI_API_KEY environment variable."
        )
