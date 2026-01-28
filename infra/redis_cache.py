# chat_bot/infra/redis_cache.py

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

# redis 패키지가 없을 수 있으니 import 실패해도 서버가 뜨도록 처리
try:
    import redis  # type: ignore
    _REDIS_AVAILABLE = True
except Exception:
    redis = None  # type: ignore
    _REDIS_AVAILABLE = False


def get_redis(redis_url: str, *, connect_timeout: float = 1.0) -> Optional["redis.Redis"]:
    """
    Redis 클라이언트 생성.
    - redis_url이 비어있거나
    - redis 패키지가 없거나
    - 연결이 안되면
    => None 반환 (서버/LLM은 계속 동작)
    """
    if not redis_url:
        return None
    if not _REDIS_AVAILABLE:
        return None

    try:
        rds = redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=connect_timeout,
            socket_timeout=connect_timeout,
        )
        # 연결 확인 (여기서 실패하면 None)
        rds.ping()
        return rds
    except Exception:
        return None


def _hist_key(session_id: str) -> str:
    return f"chat:history:{session_id}"


def get_history(rds: Optional["redis.Redis"], session_id: str) -> List[Dict[str, Any]]:
    if rds is None:
        return []
    try:
        raw = rds.get(_hist_key(session_id))
        if not raw:
            return []
        data = json.loads(raw)
        if isinstance(data, list):
            # role/content 형태만 최소 보장
            out = []
            for x in data:
                if isinstance(x, dict) and "role" in x and "content" in x:
                    out.append({"role": x["role"], "content": x["content"]})
            return out
        return []
    except Exception:
        return []


def set_history(
    rds: Optional["redis.Redis"],
    session_id: str,
    history: List[Dict[str, Any]],
    *,
    ttl_sec: int = 86400,
) -> bool:
    if rds is None:
        return False
    try:
        rds.set(_hist_key(session_id), json.dumps(history, ensure_ascii=False), ex=ttl_sec)
        return True
    except Exception:
        return False


def clear_history(rds: Optional["redis.Redis"], session_id: str) -> bool:
    if rds is None:
        return False
    try:
        rds.delete(_hist_key(session_id))
        return True
    except Exception:
        return False
