# server/broadcast.py
from __future__ import annotations
from typing import Any, Dict, Set, Tuple
from fastapi import WebSocket
import asyncio, json, math

# 연결된 구독자
subscribers: Set[WebSocket] = set()

# 브로드캐스트 작업 큐 (event, data)
_queue: "asyncio.Queue[Tuple[str, Any]]" = asyncio.Queue()

def _finite_or_none(v: Any):
    if isinstance(v, (int, float)):
        try:
            fv = float(v)
            if math.isfinite(fv):
                return fv
            return None
        except Exception:
            return None
    return v

def sanitize(event: str, data: Any) -> Any:
    # 숫자 무한대/NaN 방지 및 직렬화 안전화
    if isinstance(data, dict):
        return {k: sanitize(event, v) for k, v in data.items()}
    if isinstance(data, list):
        return [sanitize(event, x) for x in data]
    return _finite_or_none(data)

async def _broadcast(event: str, payload: Any):
    # dead connection 제거하며 전송
    dead = []
    msg = json.dumps({"event": event, "data": payload}, default=str, ensure_ascii=False)
    for ws in list(subscribers):
        try:
            await ws.send_text(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        subscribers.discard(ws)

def enqueue(event: str, data: Any):
    """폴러/서비스 코드에서 호출: 큐에 적재(논블로킹)"""
    _queue.put_nowait((event, data))

async def ws_writer():
    """큐의 메시지를 소비해 정규화 후 브로드캐스트"""
    while True:
        event, data = await _queue.get()
        try:
            safe = sanitize(event, data)
            await _broadcast(event, safe)
        except Exception as e:
            print("[ws_writer] send error:", e, "event=", event)
        finally:
            _queue.task_done()
