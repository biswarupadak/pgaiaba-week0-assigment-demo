"""ChatSession: one customer conversation about one order, driven turn by turn."""

from dataclasses import dataclass, field

from .graph import build_graph
from .memory import ConversationMemory
from .state import OrderState, new_turn_state


@dataclass
class TurnResult:
    reply: str
    ended: bool
    state: OrderState


@dataclass
class ChatSession:
    cust_id: str
    order_id: str
    debug: bool = False
    memory: ConversationMemory = field(default_factory=ConversationMemory)
    ended: bool = False

    def __post_init__(self):
        self._graph = build_graph(debug=self.debug)

    def ask(self, query: str) -> TurnResult:
        if self.ended:
            raise RuntimeError("This conversation has ended; start a new session.")

        state = new_turn_state(self.cust_id, self.order_id, query, self.memory.get())
        result = self._graph.invoke(state)

        # memory_save only runs for replies that passed every guardrail.
        self.memory.history = list(result["history"])
        self.ended = result["ended"]
        return TurnResult(reply=result["final_response"], ended=self.ended, state=result)
