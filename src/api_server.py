from datetime import datetime
from typing import Any

from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select

from src.conversation import Conversation
from src.database.models import conversations, metadata
from src.database.utils import get_engine, init_engine
from src.user_profile import UserProfile


load_dotenv("/Users/wnowogor/PycharmProjects/rag/.env")


class UserCreate(BaseModel):
    name: str = Field(min_length=1)


class UserResponse(BaseModel):
    id: int
    name: str


class ConversationCreate(BaseModel):
    user_id: int


class MessageCreate(BaseModel):
    content: str = Field(min_length=1)


class MessageResponse(BaseModel):
    role: str
    content: str
    timestamp: str


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    messages: list[MessageResponse]


class ConversationListItem(BaseModel):
    id: int
    user_id: int
    last_message: MessageResponse | None


class MessagesResponse(BaseModel):
    conversation_id: int
    messages: list[MessageResponse]


class SendMessageResponse(BaseModel):
    conversation_id: int
    assistant: MessageResponse
    messages: list[MessageResponse]


app = FastAPI(title="Chat API", version="1.0.0")


@app.on_event("startup")
def startup() -> None:
    engine = init_engine()
    metadata.create_all(engine)


def _as_message_list(data: dict[str, Any]) -> list[MessageResponse]:
    messages = data.get("messages") or []
    return [MessageResponse(**msg) for msg in messages]


@app.post("/api/v1/users", response_model=UserResponse, status_code=201)
def create_user(payload: UserCreate) -> UserResponse:
    profile = UserProfile(name=payload.name)
    user_id = profile.save()
    return UserResponse(id=user_id, name=profile.name)


@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int) -> UserResponse:
    try:
        profile = UserProfile.load(user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    assert profile.id is not None
    return UserResponse(id=profile.id, name=profile.name)


@app.post("/api/v1/conversations", response_model=ConversationResponse, status_code=201)
def create_conversation(payload: ConversationCreate) -> ConversationResponse:
    try:
        UserProfile.load(payload.user_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    conversation = Conversation(user_id=payload.user_id)
    conversation_id = conversation.save()
    return ConversationResponse(
        id=conversation_id,
        user_id=conversation.user_id,
        messages=_as_message_list(conversation.data),
    )


@app.get("/api/v1/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: int) -> ConversationResponse:
    try:
        conversation = Conversation.load(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if conversation.id is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        messages=_as_message_list(conversation.data),
    )


@app.get("/api/v1/conversations", response_model=list[ConversationListItem])
def list_conversations(user_id: int = Query(...)) -> list[ConversationListItem]:
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            select(conversations.c.id, conversations.c.user_id, conversations.c.data)
            .where(conversations.c.user_id == user_id)
            .order_by(conversations.c.id.asc())
        ).all()

    items: list[ConversationListItem] = []
    for row in rows:
        messages = row.data.get("messages") or []
        last_message = messages[-1] if messages else None
        items.append(
            ConversationListItem(
                id=row.id,
                user_id=row.user_id,
                last_message=MessageResponse(**last_message) if last_message else None,
            )
        )
    return items


@app.get("/api/v1/conversations/{conversation_id}/messages", response_model=MessagesResponse)
def get_messages(conversation_id: int) -> MessagesResponse:
    try:
        conversation = Conversation.load(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if conversation.id is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return MessagesResponse(
        conversation_id=conversation.id,
        messages=_as_message_list(conversation.data),
    )


@app.post(
    "/api/v1/conversations/{conversation_id}/messages",
    response_model=SendMessageResponse,
)
def send_message(conversation_id: int, payload: MessageCreate) -> SendMessageResponse:
    try:
        conversation = Conversation.load(conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        response = conversation.invoke(payload.content)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Model invocation failed: {exc}",
        ) from exc
    messages = _as_message_list(conversation.data)
    assistant_message = MessageResponse(
        role="assistant",
        content=response,
        timestamp=datetime.utcnow().isoformat(),
    )
    if messages:
        assistant_message = messages[-1]

    if conversation.id is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return SendMessageResponse(
        conversation_id=conversation.id,
        assistant=assistant_message,
        messages=messages,
    )
