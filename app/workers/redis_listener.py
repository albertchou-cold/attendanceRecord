from __future__ import annotations

import json
import logging
import threading
import time

from app.config import get_settings
from app.workers.redis_scv import get_redis_client


_listener_thread: threading.Thread | None = None
_pubsub = None
_stop_event = threading.Event()
logger = logging.getLogger(__name__)


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
    global _pubsub
    settings = get_settings()
    redis_client = get_redis_client()
    channel = settings.REDIS_CHANNEL
    pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
    _pubsub = pubsub
    pubsub.subscribe(channel)

    while not _stop_event.is_set():
        try:
            item = pubsub.get_message(timeout=1.0)
        except Exception as exc:
            if _stop_event.is_set():
                break
            logger.warning("redis listener read failed, reconnecting: %s", exc)
            try:
                pubsub.close()
            except Exception:
                pass

            time.sleep(1.0)
            redis_client = get_redis_client()
            pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
            _pubsub = pubsub
            pubsub.subscribe(channel)
            continue

        if item is None:
            continue
        if not isinstance(item, dict):
            continue
        if item.get("type") != "message":
            continue
        msg = item.get("data")
        if msg is None:
            continue
        try:
            _handle_message(channel=channel, message=str(msg))
        except Exception as exc:
            logger.exception("redis listener handle message failed: %s", exc)

    try:
        pubsub.close()
    except Exception:
        pass


def start_redis_listener() -> None:
    global _listener_thread
    if _listener_thread and _listener_thread.is_alive():
        return

    _stop_event.clear()
    _listener_thread = threading.Thread(target=_listen_forever, name="redis-listener", daemon=True)
    _listener_thread.start()


def stop_redis_listener() -> None:
    global _listener_thread, _pubsub
    _stop_event.set()
    if _pubsub is not None:
        try:
            _pubsub.close()
        except Exception:
            pass
        _pubsub = None

    if _listener_thread and _listener_thread.is_alive():
        _listener_thread.join(timeout=2.0)
    _listener_thread = None