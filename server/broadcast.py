# broadcast.py
from typing import Set, Any, Dict
from fastapi import WebSocket
import json, math

subscribers: Set[WebSocket] = set()

def _finite_or_none(v: Any):
    # 숫자면 유한성 체크, 그 외는 그대로(None 등)
    if isinstance(v, (int, float)):
        return v if math.isfinite(float(v)) else None
    return v

def sanitize_candle(data: Dict[str, Any]) -> Dict[str, Any]:
    # 필요 키만 추출/정규화: x, open, high, low, close
    return {
        "x": data.get("x"),
        "open": _finite_or_none(data.get("open")),
        "high": _finite_or_none(data.get("high")),
        "low":  _finite_or_none(data.get("low")),
        "close":_finite_or_none(data.get("close")),
    }

async def broadcast(event: str, data: Any):
    """
    모든 구독자에게 안전한 JSON으로 전송.
    NaN/Inf가 남아있으면 직렬화 단계에서 에러를 발생시켜 버그를 조기 발견.
    """
    payload = {"event": event, "data": data}
    try:
        message = json.dumps(payload, ensure_ascii=False, allow_nan=False)  # 🔒 NaN 차단
    except ValueError as e:
        # 개발 중 바로 원인 파악을 위해 예외를 올려도 되고,
        # 또는 여기서 한번 더 None 치환을 시도할 수도 있음.
        raise RuntimeError(f"Non-finite number in payload: {e}; payload={payload!r}")

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
