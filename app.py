# chat_bot/app.py

import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.settings import Settings
from core.logging import append_jsonl, now_utc_iso
from core.llm import call_vllm
from infra.redis_cache import get_redis, get_history, set_history, clear_history
from rag.retrieval import retrieve_context
from rag.prompt import build_messages

app = FastAPI()
S = Settings()


class ChatReq(BaseModel):
    message: str
    session_id: Optional[str] = None


@app.get("/health")
def health():
    return {"ok": True, "mode": S.chat_mode}


@app.post("/chat")
def chat(req: ChatReq):
    req_id = str(uuid.uuid4())
    sid = req.session_id or "default"

    append_jsonl(
        {
            "ts": now_utc_iso(),
            "request_id": req_id,
            "session_id": sid,
            "role": "user",
            "content": req.message,
            "meta": {"mode": S.chat_mode},
        },
        path=S.chat_log_path,
        enable=S.chat_log_enable,
    )

    # /reset: redis가 없어도 "안내"하고 정상 응답
    if req.message.strip() == "/reset":
        rds = get_redis(S.redis_url)
        if rds is None:
            answer = "OK. (Redis 미연결) 초기화할 대화 메모리가 없습니다."
        else:
            clear_history(rds, sid)
            answer = "OK. 대화 기록을 초기화했어."

        append_jsonl(
            {
                "ts": now_utc_iso(),
                "request_id": req_id,
                "session_id": sid,
                "role": "assistant",
                "content": answer,
                "meta": {"mode": "local", "kind": "reset"},
            },
            path=S.chat_log_path,
            enable=S.chat_log_enable,
        )
        return {"answer": answer, "meta": {"mode": "local", "kind": "reset"}, "request_id": req_id, "session_id": sid}

    # mock
    if S.chat_mode == "mock":
        answer = f"받은 메시지: {req.message}"
        append_jsonl(
            {
                "ts": now_utc_iso(),
                "request_id": req_id,
                "session_id": sid,
                "role": "assistant",
                "content": answer,
                "meta": {"mode": "mock"},
            },
            path=S.chat_log_path,
            enable=S.chat_log_enable,
        )
        return {"answer": answer, "meta": {"mode": "mock"}, "request_id": req_id, "session_id": sid}

    # llm
    try:
        # Redis: 연결 안되면 None 반환(=안전하게 계속 진행)
        rds = get_redis(S.redis_url)
        redis_ok = rds is not None
        history = get_history(rds, sid)  # rds=None이면 [] 반환

        # RAG: DB 미연결/드라이버 없음/연결 실패해도 ctx dict는 항상 반환
        ctx = retrieve_context(S.database_url, req.message)
        rag_status = (ctx.get("rag") or {}).get("status", "disabled")
        rag_ok = rag_status == "ok"

        # 시스템 상태 안내(유저에게 보여주되, 답변은 정상 생성)
        notices = []
        if not redis_ok:
            notices.append("- Redis(대화 메모리): 미연결")
        if not rag_ok:
            reason = (ctx.get("rag") or {}).get("reason", "")
            if reason:
                notices.append(f"- RAG(DB): 미연결/비활성 ({reason})")
            else:
                notices.append("- RAG(DB): 미연결/비활성")

        prefix = ""
        if notices:
            prefix = "[시스템 상태]\n" + "\n".join(notices) + "\n\n"

        # LLM 호출
        messages = build_messages(S.system_default, history, req.message, ctx)
        answer = call_vllm(S.vllm_base, S.vllm_model, messages)

        # 유저에겐 상태 안내 + 답변을 보여줌
        final_answer = prefix + answer

        # history 저장은 “순수 답변”만 (안내문 반복 방지)
        new_hist = (history + [{"role": "user", "content": req.message}, {"role": "assistant", "content": answer}])[
            -S.history_max_messages :
        ]
        set_history(rds, sid, new_hist, ttl_sec=86400)

        append_jsonl(
            {
                "ts": now_utc_iso(),
                "request_id": req_id,
                "session_id": sid,
                "role": "assistant",
                "content": final_answer,
                "meta": {
                    "mode": "llm",
                    "model": S.vllm_model,
                    "redis_ok": redis_ok,
                    "rag_status": rag_status,
                },
            },
            path=S.chat_log_path,
            enable=S.chat_log_enable,
        )

        return {
            "answer": final_answer,
            "meta": {"mode": "llm", "model": S.vllm_model, "redis_ok": redis_ok, "rag_status": rag_status},
            "request_id": req_id,
            "session_id": sid,
        }

    except Exception as e:
        append_jsonl(
            {
                "ts": now_utc_iso(),
                "request_id": req_id,
                "session_id": sid,
                "role": "error",
                "content": str(e),
                "meta": {"mode": "llm", "model": S.vllm_model},
            },
            path=S.chat_log_path,
            enable=S.chat_log_enable,
        )
        raise HTTPException(status_code=502, detail=f"LLM 호출 실패: {e}")
