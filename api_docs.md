## API Overview (v1)

Core endpoints mirror the data structures in `Conversation` and `UserProfile`.

### Users

- `POST /api/v1/users`
  - Body: `{ "name": "Jan" }`
  - Response: `{ "id": 1, "name": "Jan" }`
- `GET /api/v1/users/{user_id}`
  - Response: `{ "id": 1, "name": "Jan" }`

### Conversations

- `POST /api/v1/conversations`
  - Body: `{ "user_id": 1 }`
  - Response: `{ "id": 10, "user_id": 1, "messages": [] }`
- `GET /api/v1/conversations/{conversation_id}`
  - Response: `{ "id": 10, "user_id": 1, "messages": [ ... ] }`
- `GET /api/v1/conversations?user_id=1`
  - Response: list of user conversations (metadata + last message)

### Messages

- `POST /api/v1/conversations/{conversation_id}/messages`
  - Body: `{ "content": "Hello!" }`
  - Response:
    ```json
    {
      "conversation_id": 10,
      "assistant": {
        "role": "assistant",
        "content": "Hi! How can I help?",
        "timestamp": "2026-02-05T12:34:56.789Z"
      },
      "messages": [ ... full history ... ]
    }
    ```
- `GET /api/v1/conversations/{conversation_id}/messages`
  - Response: `{ "conversation_id": 10, "messages": [ ... full history ... ] }`

## Data Models

### Message

```
{
  "role": "user|assistant",
  "content": "string",
  "timestamp": "ISO8601"
}
```

### Conversation

```
{
  "id": 10,
  "user_id": 1,
  "messages": [Message...]
}
```

### User

```
{
  "id": 1,
  "name": "Jan"
}
```

## Status Codes

- `200/201` – success
- `400` – invalid input (e.g. missing `content`)
- `404` – user or conversation not found
