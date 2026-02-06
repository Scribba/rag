import os
from typing import Any, TypedDict, cast

import requests
import streamlit as st

DEFAULT_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8002")


class MessagePayload(TypedDict, total=False):
    role: str
    content: str
    timestamp: str


class ConversationItem(TypedDict):
    id: int
    user_id: int
    last_message: MessagePayload | None


class UserPayload(TypedDict):
    id: int
    name: str


class MessagesPayload(TypedDict):
    conversation_id: int
    messages: list[MessagePayload]


class SendMessagePayload(MessagesPayload):
    assistant: MessagePayload


def init_state() -> None:
    st.session_state.setdefault("api_base_url", DEFAULT_BASE_URL)
    st.session_state.setdefault("user_id", None)
    st.session_state.setdefault("user_name", None)
    st.session_state.setdefault("conversations", [])
    st.session_state.setdefault("active_conversation_id", None)
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("messages_loaded_for", None)


def clear_user_state() -> None:
    st.session_state["user_id"] = None
    st.session_state["user_name"] = None
    st.session_state["conversations"] = []
    st.session_state["active_conversation_id"] = None
    st.session_state["messages"] = []
    st.session_state["messages_loaded_for"] = None


def api_request(
    method: str,
    path: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any] | list[dict[str, Any]] | None:
    base_url = st.session_state["api_base_url"].rstrip("/")
    url = f"{base_url}{path}"
    try:
        response = requests.request(
            method,
            url,
            json=json,
            params=params,
            timeout=30,
        )
    except requests.RequestException as exc:
        st.error(f"API request failed: {exc}")
        return None

    if not response.ok:
        detail = response.text
        try:
            detail = response.json().get("detail", detail)
        except ValueError:
            pass
        st.error(f"API error {response.status_code}: {detail}")
        return None

    try:
        payload = response.json()
    except ValueError:
        st.error("API returned invalid JSON.")
        return None
    if isinstance(payload, dict):
        return cast(dict[str, Any], payload)
    if isinstance(payload, list):
        return cast(list[dict[str, Any]], payload)
    st.error("API returned unexpected payload type.")
    return None


def load_conversations() -> None:
    user_id = st.session_state["user_id"]
    if user_id is None:
        return
    data = api_request(
        "GET",
        "/api/v1/conversations",
        params={"user_id": user_id},
    )
    if data is None:
        return
    if not isinstance(data, list):
        st.error("Conversation list payload is invalid.")
        return
    st.session_state["conversations"] = data


def load_messages(conversation_id: int) -> None:
    data = api_request(
        "GET",
        f"/api/v1/conversations/{conversation_id}/messages",
    )
    if data is None:
        return
    if not isinstance(data, dict):
        st.error("Messages payload is invalid.")
        return
    messages_payload = cast(MessagesPayload, data)
    st.session_state["messages"] = messages_payload.get("messages", [])
    st.session_state["messages_loaded_for"] = conversation_id


def set_active_conversation(conversation_id: int | None) -> None:
    st.session_state["active_conversation_id"] = conversation_id
    st.session_state["messages"] = []
    st.session_state["messages_loaded_for"] = None


def register_user(name: str) -> None:
    data = api_request("POST", "/api/v1/users", json={"name": name})
    if data is None:
        return
    if not isinstance(data, dict):
        st.error("User payload is invalid.")
        return
    user_payload = cast(UserPayload, data)
    st.session_state["user_id"] = user_payload["id"]
    st.session_state["user_name"] = user_payload["name"]
    load_conversations()


def login_user(user_id: int) -> None:
    data = api_request("GET", f"/api/v1/users/{user_id}")
    if data is None:
        return
    if not isinstance(data, dict):
        st.error("User payload is invalid.")
        return
    user_payload = cast(UserPayload, data)
    st.session_state["user_id"] = user_payload["id"]
    st.session_state["user_name"] = user_payload["name"]
    load_conversations()


def create_conversation() -> None:
    user_id = st.session_state["user_id"]
    if user_id is None:
        return
    data = api_request("POST", "/api/v1/conversations", json={"user_id": user_id})
    if data is None:
        return
    if not isinstance(data, dict):
        st.error("Conversation payload is invalid.")
        return
    set_active_conversation(cast(int, data.get("id")))
    load_conversations()


def send_message(content: str) -> None:
    conversation_id = st.session_state["active_conversation_id"]
    if conversation_id is None:
        return
    data = api_request(
        "POST",
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": content},
    )
    if data is None:
        return
    if not isinstance(data, dict):
        st.error("Message payload is invalid.")
        return
    send_payload = cast(SendMessagePayload, data)
    st.session_state["messages"] = send_payload.get("messages", [])
    st.session_state["messages_loaded_for"] = conversation_id
    load_conversations()


def render_sidebar() -> None:
    st.sidebar.title("Chat App")

    base_url = st.sidebar.text_input("API base URL", st.session_state["api_base_url"])
    if base_url and base_url != st.session_state["api_base_url"]:
        st.session_state["api_base_url"] = base_url
        clear_user_state()
        st.sidebar.info("API base URL changed. Please log in again.")

    user_id = st.session_state["user_id"]
    if user_id is None:
        tabs = st.sidebar.tabs(["Register", "Login"])
        with tabs[0]:
            name = st.text_input("Name", key="register_name")
            if st.button("Create account"):
                if name.strip():
                    register_user(name.strip())
                    st.rerun()
                else:
                    st.warning("Name is required.")
        with tabs[1]:
            login_id = st.text_input("User ID", key="login_id")
            if st.button("Login"):
                if login_id.isdigit():
                    login_user(int(login_id))
                    st.rerun()
                else:
                    st.warning("User ID must be a number.")
        return

    st.sidebar.success(f"Logged in as {st.session_state['user_name']} (#{user_id})")
    if st.sidebar.button("Logout"):
        clear_user_state()
        st.rerun()
        return

    if st.sidebar.button("New conversation"):
        create_conversation()
        st.rerun()

    if st.sidebar.button("Refresh conversations"):
        load_conversations()

    conversations = st.session_state["conversations"]
    if not conversations:
        st.sidebar.info("No conversations yet.")
        return

    items_by_id = {cast(ConversationItem, item)["id"]: cast(ConversationItem, item)
                   for item in conversations}
    options = list(items_by_id.keys())
    active_id = st.session_state["active_conversation_id"]
    index = options.index(active_id) if active_id in options else 0

    def format_conv(conv_id: int) -> str:
        item = items_by_id[conv_id]
        last = item.get("last_message")
        preview = "No messages yet"
        if last and last.get("content"):
            preview = last["content"][:50]
        return f"#{conv_id} — {preview}"

    selected = st.sidebar.radio(
        "Conversations",
        options=options,
        index=index,
        format_func=format_conv,
    )
    if selected != active_id:
        set_active_conversation(selected)


def render_messages() -> None:
    conversation_id = st.session_state["active_conversation_id"]
    if conversation_id is None:
        st.info("Select or create a conversation to begin.")
        return

    if st.session_state["messages_loaded_for"] != conversation_id:
        load_messages(conversation_id)

    for msg in st.session_state["messages"]:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        st.chat_message(role).write(content)

    prompt = st.chat_input("Type a message")
    if prompt:
        send_message(prompt)
        st.rerun()


def main() -> None:
    st.set_page_config(page_title="Chat App", layout="wide")
    init_state()
    render_sidebar()

    if st.session_state["user_id"] is None:
        st.title("Welcome")
        st.write("Register or log in to start chatting.")
        return

    st.title("Conversations")
    render_messages()


if __name__ == "__main__":
    main()
