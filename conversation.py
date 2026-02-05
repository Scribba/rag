from typing import TypedDict, Annotated

import os
import sqlite3
import uuid
from langchain.chat_models import init_chat_model
from langchain_core.messages.utils import (
    trim_messages,
    count_tokens_approximately,
)
from langchain_core.messages import HumanMessage, BaseMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages


_DB_PATH = os.path.join(os.path.dirname(__file__), "db.sqlite3")
checkpointer = SqliteSaver(sqlite3.connect(_DB_PATH, check_same_thread=False))


class ConversationState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]


def call_model_trim(state: ConversationState):
    model = init_chat_model("gpt-4.1-mini")
    messages = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=128,
        start_on="human",
        end_on=("human", "tool"),
    )
    response = model.invoke(messages)
    return {"messages": [response]}


class Conversation:
    def __init__(self, conversation_id: str | None = None):
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
        self.config = {"configurable": {"thread_id": conversation_id}}

        builder = StateGraph(ConversationState)
        builder.add_node("generate", call_model_trim)
        builder.add_edge(START, "generate")
        builder.add_edge("generate", END)
        self.graph = builder.compile(checkpointer=checkpointer)

    def invoke(self, message: str):
        init_state = {"messages": [HumanMessage(message)]}
        return self.graph.invoke(init_state, config=self.config)


if __name__ == '__main__':
    from dotenv import load_dotenv

    load_dotenv("/Users/wnowogor/PycharmProjects/rag/.env")


    conversation = Conversation()
    conversation.invoke("HI ")

    conversation.invoke("How are you?")

    conversation.invoke("Gfdsgdf")

    conversation = Conversation(conversation_id="123")
    conversation.invoke("HWDP")


