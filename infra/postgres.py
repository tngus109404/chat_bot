from typing import List, Dict, Any

try:
    import psycopg
except Exception:
    psycopg = None

def _require_psycopg():
    if psycopg is None:
        raise RuntimeError("psycopg 패키지가 없습니다. pip install 'psycopg[binary]' 로 설치하세요.")

def fetch_recent_prices(database_url: str, commodity: str, days: int = 14) -> List[Dict[str, Any]]:
    """
    ✅ 예시 쿼리 (너희 스키마에 맞게 수정)
    - prices_daily(commodity text, dt date, close numeric, change_pct numeric)
    """
    if not database_url:
        return []
    _require_psycopg()

    sql = """
    SELECT commodity, dt, close, change_pct
    FROM prices_daily
    WHERE commodity = %s
      AND dt >= (CURRENT_DATE - %s::int)
    ORDER BY dt DESC
    LIMIT 30;
    """

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (commodity, days))
            rows = cur.fetchall()

    out = []
    for commodity, dt, close, change_pct in rows:
        out.append({
            "commodity": commodity,
            "dt": str(dt),
            "close": float(close) if close is not None else None,
            "change_pct": float(change_pct) if change_pct is not None else None,
        })
    return out

def search_news(database_url: str, commodity: str, days: int = 14, limit: int = 6) -> List[Dict[str, Any]]:
    """
    ✅ 예시 쿼리 (너희 스키마에 맞게 수정)
    - news(commodity text, published_at timestamptz, title text, source text, url text, summary text)
    """
    if not database_url:
        return []
    _require_psycopg()

    sql = """
    SELECT published_at, title, source, url, summary
    FROM news
    WHERE commodity = %s
      AND published_at >= (NOW() - (%s || ' days')::interval)
    ORDER BY published_at DESC
    LIMIT %s;
    """

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (commodity, days, limit))
            rows = cur.fetchall()

    out = []
    for published_at, title, source, url, summary in rows:
        out.append({
            "published_at": published_at.isoformat() if published_at else None,
            "title": title,
            "source": source,
            "url": url,
            "summary": summary,
        })
    return out
