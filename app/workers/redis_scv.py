from __future__ import annotations

import redis

from app.config import get_settings


def get_redis_client() -> redis.Redis:
    settings = get_settings()
    kwargs = {"decode_responses": True}
    if settings.REDIS_SSL_INSECURE:
        kwargs["ssl_cert_reqs"] = None
    return redis.from_url(settings.REDIS_URL, **kwargs)