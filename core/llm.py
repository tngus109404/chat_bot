import re
import requests
from typing import List, Dict

# ✅ 한자(중국어) + 일본어(히라가나/가타카나/반각 가타카나) 감지
# - CJK Unified Ideographs: 4E00-9FFF
# - CJK Extension A: 3400-4DBF
# - CJK Compatibility Ideographs: F900-FAFF
# - Hiragana/Katakana: 3040-30FF
# - Katakana Phonetic Extensions: 31F0-31FF
# - Halfwidth Katakana: FF66-FF9D
CJK_JP_RE = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\u3040-\u30FF\u31F0-\u31FF\uFF66-\uFF9D]")

def _post(vllm_base: str, payload: dict, timeout: int) -> str:
    r = requests.post(f"{vllm_base}/v1/chat/completions", json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]

def call_vllm(vllm_base: str, vllm_model: str, messages: List[Dict], timeout: int = 90) -> str:
    payload = {
        "model": vllm_model,
        "messages": messages,
        "temperature": 0.4,
        "top_p": 0.8,
        "max_tokens": 400,
    }

    answer = _post(vllm_base, payload, timeout)

    # ✅ 한자/일본어 섞이면 1회 재시도
    if CJK_JP_RE.search(answer or ""):
        retry_messages = messages + [{
            "role": "system",
            "content": (
                "방금 답변에 한자/일본어가 섞였다. "
                "한자(중국어)와 일본어(히라가나/가타카나)를 절대 쓰지 말고 "
                "한국어 중심으로 다시 답해. 영어 단어는 필요하면 써도 된다."
            )
        }]
        payload["messages"] = retry_messages
        return _post(vllm_base, payload, timeout)

    return answer
