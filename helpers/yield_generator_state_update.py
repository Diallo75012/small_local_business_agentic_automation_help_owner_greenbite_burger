from langgraph.graph import MessagesState
from typing import Dict

def update_state_gen(state: MessagesState, new_message: Dict) -> MessagesState:
    # Force state re-assignment and yield the new state
    state["messages"] = state["messages"] + [new_message]
    yield state
