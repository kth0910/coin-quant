# broadcast.py
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
        except Exception:
            return None
        return fv if math.isfinite(fv) else None
    return v

def sanitize_candle(data: Dict[str, Any]) -> Dict[str, Any]:
    # 필요한 키만 추려서 NaN/Inf → None
    return {
        "x": data.get("x"),
        "open": _finite_or_none(data.get("open")),
        "high": _finite_or_none(data.get("high")),
        "low":  _finite_or_none(data.get("low")),
        "close":_finite_or_none(data.get("close")),
    }

def sanitize(event: str, data: Any) -> Any:
    # 이벤트별 정규화 룰(필요 시 확장)
    if event == "history" and isinstance(data, dict):
        return sanitize_candle(data)
    return data

async def _broadcast(event: str, data: Any):
    """실제 송신 (allow_nan=False로 비표준 값 차단)"""
    payload = {"event": event, "data": data}
    # NaN/Inf가 남아 있으면 여기서 바로 에러가 나서 원인 파악 쉬움
    message = json.dumps(payload, ensure_ascii=False, allow_nan=False)

    dead = []
    for ws in list(subscribers):
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        try:
            await ws.close()
        finally:
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
            print("[ws_writer] sended data : ", safe)
            await _broadcast(event, safe)
        except Exception as e:
            # 개발 중 원인 확인
            print("[ws_writer] send error:", e, "event=", event, "data=", data)
        finally:
            _queue.task_done()
