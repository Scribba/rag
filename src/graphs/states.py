from typing import TypedDict, Any, NotRequired


class ConversationState(TypedDict):
    messages: list[dict[str, str]]
    user_profile: dict[str, Any]
    response: NotRequired[str]