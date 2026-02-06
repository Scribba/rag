from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime

from sqlalchemy import select

from src.database.utils import get_engine
from src.database.models import conversations
from src.graphs.simple_generation_graph import SimpleGenerationGraph
from src.user_profile import UserProfile


@dataclass
class Conversation:
    user_id: int
    id: Optional[int] = None
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if "messages" not in self.data:
            self.data["messages"] = []

    def to_dict(self) -> dict[str, Any]:
        return self.data

    @classmethod
    def from_dict(
        cls,
        user_id: int,
        data: dict[str, Any],
        id: Optional[int] = None,
    ) -> "Conversation":
        return cls(user_id=user_id, data=data, id=id)

    def save(self) -> int:
        engine = get_engine()
        with engine.begin() as conn:
            if self.id is None:
                result = conn.execute(
                    conversations.insert().values(user_id=self.user_id, data=self.to_dict())
                )
                inserted = result.inserted_primary_key
                if not inserted:
                    raise RuntimeError("Failed to insert conversation")
                self.id = inserted[0]
            else:
                conn.execute(
                    conversations.update()
                    .where(conversations.c.id == self.id)
                    .values(user_id=self.user_id, data=self.to_dict())
                )
        return self.id

    @classmethod
    def load(cls, conversation_id: int) -> "Conversation":
        engine = get_engine()
        with engine.connect() as conn:
            row = conn.execute(
                select(conversations.c.user_id, conversations.c.data)
                .where(conversations.c.id == conversation_id)
            ).one_or_none()
            if row is None:
                raise KeyError(f"No conversation with id={conversation_id}")
            return cls.from_dict(row.user_id, row.data, id=conversation_id)

    def invoke(self, message: str) -> str:
        self.data["messages"].append(
            {
                "role": "user",
                "content": message,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        user_profile = UserProfile.load(self.user_id).to_dict()
        messages = self.data["messages"]

        response = SimpleGenerationGraph().invoke(messages, user_profile)

        self.data["messages"].append(
            {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        self.save()
        return response

