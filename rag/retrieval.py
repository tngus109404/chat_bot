# chat_bot/rag/retrieval.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

# (선택) Postgres 드라이버가 없을 수도 있으니 안전하게 처리
try:
    import psycopg  # psycopg3
    _PG_AVAILABLE = True
except Exception:
    psycopg = None  # type: ignore
    _PG_AVAILABLE = False


def retrieve_context(database_url: Optional[str], user_query: str) -> Dict[str, Any]:
    """
    RAG 컨텍스트를 "항상 dict"로 반환.
    - DB 미설정/드라이버 없음/연결 실패: rag.status != ok, 컨텍스트는 빈 값
    - 연결 성공: rag.status=ok (단, 실제 쿼리는 스키마 확정 후 TODO로 채워넣기)
    """
    ctx: Dict[str, Any] = {
        "rag": {
            "status": "disabled",  # disabled | driver_missing | error | ok
            "reason": "",
        },
        "price": {
            "summary": "",
            "rows": [],  # 필요하면 [{...}, ...]
        },
        "news": {
            "snippets": [],  # 필요하면 [{"title":..., "date":..., "source":..., "text":...}, ...]
        },
    }

    if not database_url:
        ctx["rag"]["status"] = "disabled"
        ctx["rag"]["reason"] = "DATABASE_URL이 설정되지 않았습니다."
        return ctx

    if not _PG_AVAILABLE:
        ctx["rag"]["status"] = "driver_missing"
        ctx["rag"]["reason"] = "psycopg 패키지가 없습니다. (pip install psycopg[binary])"
        return ctx

    # 연결만 확인 (스키마/쿼리는 팀이 확정되면 여기서 구현)
    try:
        with psycopg.connect(database_url, connect_timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                _ = cur.fetchone()

        ctx["rag"]["status"] = "ok"
        ctx["rag"]["reason"] = "DB 연결은 성공했지만, 실제 retrieval 쿼리는 아직 미구현(TODO)입니다."

        # TODO(나중에): 스키마 확정 후 아래를 구현
        # ctx["price"]["rows"] = query_latest_prices(conn, ...)
        # ctx["price"]["summary"] = summarize_prices(...)
        # ctx["news"]["snippets"] = query_relevant_news(conn, user_query, ...)

        return ctx

    except Exception as e:
        ctx["rag"]["status"] = "error"
        ctx["rag"]["reason"] = f"DB 연결 실패: {e}"
        return ctx
