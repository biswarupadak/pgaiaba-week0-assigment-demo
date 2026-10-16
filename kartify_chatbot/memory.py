"""Conversation memory kept across turns within one chat session."""

from typing import Dict, List


class ConversationMemory:
    def __init__(self):
        self.history: List[Dict[str, str]] = []

    def add(self, user: str, assistant: str) -> None:
        """Record one user/assistant exchange."""
        self.history.append({"user": user, "assistant": assistant})

    def get(self) -> List[Dict[str, str]]:
        """Return a copy of the full chat history."""
        return list(self.history)

    def clear(self) -> None:
        self.history = []

    def as_text(self) -> str:
        """Render history as a transcript for prompts."""
        return "\n".join(
            f"User: {h['user']}\nAssistant: {h['assistant']}" for h in self.history
        )
