from __future__ import annotations

from typing import Any, Dict, List


def _render_context(ctx: Dict[str, Any]) -> str:
    """
    ctx(dict) -> LLM에 넣을 근거 텍스트.
    비어있으면 "" 반환.
    """
    if not isinstance(ctx, dict):
        return ""

    price = ctx.get("price") if isinstance(ctx.get("price"), dict) else {}
    news = ctx.get("news") if isinstance(ctx.get("news"), dict) else {}

    parts: List[str] = []

    # 가격 요약(선택)
    price_summary = (price.get("summary") or "").strip()
    if price_summary:
        parts.append(f"[가격 요약]\n{price_summary}")

    # 뉴스 스니펫(선택)
    snippets = news.get("snippets", [])
    if isinstance(snippets, list) and snippets:
        lines = ["[관련 뉴스 근거]"]
        for i, s in enumerate(snippets[:5], 1):
            if not isinstance(s, dict):
                continue
            title = (s.get("title") or "").strip()
            date = (s.get("date") or "").strip()
            source = (s.get("source") or "").strip()
            text = (s.get("text") or "").strip()

            meta = " · ".join([x for x in [date, source] if x])
            head = f"{i}) {title or '(제목 없음)'}"
            if meta:
                head += f" ({meta})"
            if text:
                lines.append(head + f"\n- {text}")
            else:
                lines.append(head)

        parts.append("\n".join(lines))

    return "\n\n".join([p for p in parts if p]).strip()


def build_messages(
    system_default: str,
    history: List[Dict[str, str]],
    user_message: str,
    ctx: Dict[str, Any],
) -> List[Dict[str, str]]:
    """
    vLLM(OpenAI 호환) messages 구성.
    - system_default: 기본 시스템 프롬프트
    - history: redis 등에 저장된 user/assistant 히스토리
    - user_message: 이번 입력
    - ctx: retrieve_context() 결과(dict)
    """
    messages: List[Dict[str, str]] = [{"role": "system", "content": system_default}]

    ctx_text = _render_context(ctx)
    if ctx_text:
        # 근거는 system에 추가해서 "근거 기반" 답변을 유도
        messages.append({"role": "system", "content": f"아래 근거를 참고해서 답해.\n\n{ctx_text}"})

    # history 추가
    if history:
        for h in history:
            if not isinstance(h, dict):
                continue
            role = h.get("role")
            content = h.get("content")
            if role in ("user", "assistant") and isinstance(content, str):
                messages.append({"role": role, "content": content})

    # 이번 user 입력
    messages.append({"role": "user", "content": user_message})
    return messages


# (호환용) 혹시 다른 코드에서 build_prompt를 쓰면 같이 동작하게
build_prompt = build_messages

__all__ = ["build_messages", "build_prompt"]
