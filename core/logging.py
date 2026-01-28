import os
import json
import fcntl
from datetime import datetime, timezone
from typing import Dict, Any

def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def append_jsonl(record: Dict[str, Any], path: str, enable: bool = True) -> None:
    """JSONL append (락 + flush + fsync)"""
    if not enable:
        return

    line = json.dumps(record, ensure_ascii=False) + "\n"

    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)

    with open(path, "a", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.write(line)
        f.flush()
        os.fsync(f.fileno())
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
