from langgraph.graph import START, END, StateGraph
from langchain.chat_models import init_chat_model

from src.state import ConversationState


def call_model(state: ConversationState):
    model = init_chat_model("gpt-4.1-mini")
    response = model.invoke(state["messages"])
    return {"response": response.content}


class Graph:
    def __init__(self):
        builder = StateGraph(ConversationState)
        builder.add_node("generate", call_model)
        builder.add_edge(START, "generate")
        builder.add_edge("generate", END)
        self.graph = builder.compile()

    def invoke(self, messages: list[dict], user_profile: dict) -> str:
        initial_state = ConversationState(messages=messages, user_profile=user_profile)
        result = self.graph.invoke(initial_state)
        return result["response"]
