from __future__ import annotations

import json
import os
import threading

from app.workers.redis_scv import get_redis_client


_listener_thread: threading.Thread | None = None


def _handle_message(channel: str, message: str) -> None:
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        data = {"userId": "(unknown)", "raw": message}

    redis_client = get_redis_client()
    user_id = str(data.get("userId", "(unknown)"))

    redis_client.set(f"user:status:{user_id}", json.dumps(data))
    redis_client.lpush(f"logs:attendance:{user_id}", json.dumps(data))


def _listen_forever() -> None:
    redis_client = get_redis_client()
    channel = os.getenv("REDIS_CHANNEL", "state_changes")
    pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(channel)

    for item in pubsub.listen():
        if not isinstance(item, dict):
            continue
        if item.get("type") != "message":
            continue
        msg = item.get("data")
        if msg is None:
            continue
        _handle_message(channel=channel, message=str(msg))


def start_redis_listener() -> None:
    global _listener_thread
    if _listener_thread and _listener_thread.is_alive():
        return

    _listener_thread = threading.Thread(target=_listen_forever, name="redis-listener", daemon=True)
    _listener_thread.start()