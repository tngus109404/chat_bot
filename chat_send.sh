#!/usr/bin/env bash
set -euo pipefail

BASE="${CHAT_API_BASE:-http://127.0.0.1:8000}"
SESSION_FILE="${CHAT_SESSION_FILE:-.chat_session_id}"

new_session() {
  python - <<'PY'
import uuid
print(uuid.uuid4())
PY
}

ensure_session() {
  if [[ ! -f "$SESSION_FILE" ]]; then
    new_session > "$SESSION_FILE"
  fi
  cat "$SESSION_FILE"
}

send_one() {
  local sid="$1"
  local msg="$2"

  local req_json
  req_json="$(python - "$sid" "$msg" <<'PY'
import json, sys
sid = sys.argv[1]
msg = sys.argv[2]
print(json.dumps({"session_id": sid, "message": msg}, ensure_ascii=False))
PY
)"

  local resp
  resp="$(curl -sS -X POST "$BASE/chat" -H "Content-Type: application/json" -d "$req_json")"

  python - "$resp" <<'PY'
import json, sys
data = json.loads(sys.argv[1])

# 에러 응답(HTTPException detail) 처리
if "detail" in data and "answer" not in data:
    print("\n[error]")
    print(data["detail"])
    sys.exit(0)

meta = data.get("meta", {}) or {}
warnings = meta.get("warnings", []) or []
infra = meta.get("infra", {}) or {}

if warnings:
    print("\n[warnings]")
    for w in warnings:
        print(f"- {w}")

# (원하면 infra도 보여주고 싶을 때)
# if infra:
#     print("\n[infra]")
#     print(json.dumps(infra, ensure_ascii=False, indent=2))

print("\n[assistant]")
print(data.get("answer",""))
PY
}

# 옵션: 새 세션
if [[ "${1:-}" == "--new" ]]; then
  new_session > "$SESSION_FILE"
  echo "New session_id: $(cat "$SESSION_FILE")"
  exit 0
fi

sid="$(ensure_session)"

# 인자 있으면 1회 전송
if [[ $# -ge 1 ]]; then
  send_one "$sid" "$1"
  exit 0
fi

# 인자 없으면 대화형
echo "Session: $sid"
echo "(exit: 빈 줄 입력)"
while true; do
  read -r -p "> " msg || break
  [[ -z "$msg" ]] && break
  send_one "$sid" "$msg"
done
