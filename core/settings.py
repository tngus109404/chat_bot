import os
from dataclasses import dataclass

DEFAULT_SYSTEM = (
    "너는 한국어로 답하는 챗봇이다.\n"
    "아래 규칙은 절대 규칙이다.\n"
    "1) 중국어(한자)와 일본어(히라가나/가타카나)는 절대 사용하지 않는다.\n"
    "2) 영어 단어는 필요하면 써도 되지만, 가능한 한국어로 설명을 우선한다.\n"
    "3) 확신이 없으면 단정하지 말고 불확실성 표현(예: ~일 수 있습니다)을 포함한다.\n"
)

@dataclass(frozen=True)
class Settings:
    # mode
    chat_mode: str = os.getenv("CHAT_MODE", "mock")  # mock | llm

    # vLLM
    vllm_base: str = os.getenv("VLLM_BASE", "http://127.0.0.1:8001")
    vllm_model: str = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")

    # logging
    chat_log_path: str = os.getenv("CHAT_LOG_PATH", "chat_log.jsonl")
    chat_log_enable: bool = os.getenv("CHAT_LOG_ENABLE", "1") == "1"

    # db/redis
    database_url: str = os.getenv("DATABASE_URL", "")  # postgresql://user:pass@host:5432/db
    redis_url: str = os.getenv("REDIS_URL", "")        # redis://host:6379/0

    # chat memory
    history_max_messages: int = int(os.getenv("HISTORY_MAX_MESSAGES", "12"))

    # system prompt
    system_default: str = os.getenv("CHAT_SYSTEM_DEFAULT", DEFAULT_SYSTEM)
