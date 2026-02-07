from typing import Any

from langgraph.graph import START, END, StateGraph
from langchain.chat_models import init_chat_model

from src.graphs.states import ConversationState
from src.graphs.base_graph import BaseGraph


def call_model(state: ConversationState) -> dict[str, Any]:
    model = init_chat_model("gpt-4.1-mini")
    response = model.invoke(state["messages"])
    return {"response": response.content}


class SimpleGenerationGraph(BaseGraph):
    def __init__(self) -> None:
        builder = StateGraph(ConversationState)
        builder.add_node("generate", call_model)
        builder.add_edge(START, "generate")
        builder.add_edge("generate", END)
        self.graph: Any = builder.compile()

    def invoke(self, messages: list[dict[str, str]], user_profile: dict[str, Any]) -> str:
        initial_state = ConversationState(messages=messages, user_profile=user_profile)
        result = self.graph.invoke(initial_state)
        if not isinstance(result, dict):
            raise ValueError("Graph invocation returned an invalid response.")
        response = result.get("response")
        if not isinstance(response, str):
            raise ValueError("Graph response payload is missing a response string.")
        return response
