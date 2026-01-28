# 🤖 vLLM-FastAPI Chatbot (Qwen2.5-7B)

사용자 질문을 받아 **FastAPI `/chat`** 로 처리하고, **vLLM 서버(Qwen2.5-7B-Instruct)**를 호출해 답변을 생성하는 챗봇입니다.

## 🎯 주요 목표
* **vLLM 기반 고성능 추론**: Qwen2.5 모델을 활용한 고품질 답변 생성
* **RAG (Retrieval-Augmented Generation)**: PostgreSQL을 활용한 지식 근거 기반 답변 (예정)
* **세션 관리 및 캐싱**: Redis를 이용한 대화 히스토리 및 가격 정보 캐시 (예정)

---

## 🏗 아키텍처 (Architecture)


### 현재 흐름 (Current Flow)
1. **User (Terminal)**: `chat_send.sh`를 통해 질문 전송
2. **FastAPI (`/chat`)**: 요청 수신 및 로직 처리
3. **Core (`llm.py`)**: vLLM 서버(Port 8001)로 추론 요청
4. **vLLM**: Qwen2.5 모델을 통해 답변 생성
5. **Logging**: 모든 대화 내역을 `chat_log.jsonl`에 저장

---

## 📂 프로젝트 구조 (Project Structure)

```text
chat_bot/
├── app.py                 # FastAPI 엔트리포인트 (/chat)
├── chat_send.sh           # 터미널 대화 테스트 스크립트 (세션 관리)
├── core/
│   ├── settings.py        # 환경변수 및 설정 (CHAT_MODE 등)
│   ├── llm.py             # vLLM API 호출 로직
│   └── logging.py         # JSONL 로그 기록 유틸
├── infra/                 # 인프라 연결 모듈 (추후 구현)
│   ├── postgres.py        # PostgreSQL 연결/쿼리
│   └── redis_cache.py     # Redis 세션 저장
├── rag/                   # RAG 관련 로직 (추후 구현)
│   ├── retrieval.py       # 근거 검색 로직
│   └── prompt.py          # RAG 프롬프트 조립
├── chat_log.jsonl         # [Runtime] 대화 로그 (Git 제외)
└── .chat_session_id       # [Runtime] 현재 세션 상태 (Git 제외)
```
---

## ✅ 현재까지 완료 (What’s Done)
- vLLM 서버로 `Qwen/Qwen2.5-7B-Instruct` 서빙
- FastAPI 서버에서 `POST /chat`로 질문을 받아 vLLM 호출
- 터미널에서 `chat_send.sh`로 대화 테스트 가능(세션 자동 관리)
- `chat_log.jsonl`에 대화 로그 저장(JSONL)

---

## 🚀 실행 방법 (꺼졌다가 다시 켤 때)

### 1) vLLM 서버 실행 (터미널 1)
```bash
cd ~/chat_bot
source .venv_llm/bin/activate
vllm serve Qwen/Qwen2.5-7B-Instruct --host 0.0.0.0 --port 8001
```
### 2) FastAPI 서버 실행 (터미널 2)
```bash
cd ~/chat_bot
source .venv/bin/activate
CHAT_MODE=llm uvicorn app:app --host 0.0.0.0 --port 8000
```

### 3) 테스트 (터미널 3)
```bash
cd ~/chat_bot
./chat_send.sh "환율이 떨어지면 옥수수 가격이 어떻게 바뀔까?"
```

## 🧪 테스트 방법 (2가지)
### A) `chat_send.sh` (추천)

- 세션을 자동으로 관리해서 “대화 테스트”가 편합니다.
```bash
./chat_send.sh "안녕!"
./chat_send.sh "방금 말한거 다시 요약해줘."
```
`--new` 옵션

- 새 세션 ID를 만들어서 대화 히스토리(메모리)를 새로 시작합니다.
- 세션 ID는 .chat_session_id 파일로 관리됩니다. (런타임 생성 / Git 제외)

```bash
./chat_send.sh --new
./chat_send.sh "새 세션에서 안녕!"
```

### B) `curl` (디버깅용)
```bash
curl -sS -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","message":"안녕!"}'
```

## 📡 API 스펙 (API Spec)
`POST /chat`

## Request
```bash
{
  "session_id": "test",
  "message": "안녕!"
}
```

### Response (example)
```bash
{
  "session_id": "test",
  "answer": "안녕하세요! 무엇을 도와드릴까요?"
}
```
⚠️ 응답 필드명은 실제 app.py 구현에 맞게 조정하세요.


## 📝 로깅 (Logging)

- 모든 대화는 chat_log.jsonl에 JSONL 형태로 저장됩니다.

- 이 파일은 런타임에 생성되며 Git에 커밋하지 않습니다.

예시:
```bash
{"ts":"2026-01-28T12:34:56","session_id":"test","user":"안녕!","assistant":"안녕하세요!"}
```

## ⚠️ 현재 상태 / 한계 (Limitations)

지금은 DB/Redis 연결이 없어서

RAG 근거 검색 ❌

대화 기억(메모리) ❌

따라서 “이전 대화를 기억 못함”
→ Redis 연결 시 session_id 기반 히스토리/캐시로 확장 예정


## 🗺 로드맵 (Roadmap)

 Redis로 session_id 기반 대화 히스토리 저장/복원

 PostgreSQL 기반 근거 검색(RAG) 붙이기

 RAG prompt 템플릿 정리 및 근거 인용 포맷 추가

 타임아웃/재시도/에러 핸들링 강화

## 🔒 Git에 포함하지 않는 파일 (Important)

다음 파일은 런타임 생성/민감 정보일 수 있어 커밋하지 않습니다.

- `chat_log.jsonl`

- `.chat_session_id`

- `__pycache__/`

- `.env`, `.venv/`, `.venv_llm/`

`.gitignore`에 포함되어 있어야 합니다.





