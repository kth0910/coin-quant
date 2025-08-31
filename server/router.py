# server/router.py
from __future__ import annotations
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from db import get_db, SessionLocal
from models import TradingHistory, TradingReflection
from schemas import (
    TradingHistoryOut, SignalOut, HistoryResponse, LatestResponse, HealthResponse, TradingReflectionOut, ReflectionsResponse,
)
from broadcast import subscribers

api_router = APIRouter()

# --- helpers ---
def _to_signal(dto: TradingHistoryOut) -> SignalOut:
    typ = (dto.decision or "").upper()
    if typ not in {"BUY", "SELL", "HOLD", "ALERT"}:
        typ = "HOLD"
    return SignalOut(
        id=dto.id,
        ts=dto.timestamp,
        ticker="BTC/KRW",
        price=dto.btc_krw_price,
        type=typ,
        confidence=dto.percentage,
        reason=dto.reason,
    )

# --- REST ---
@api_router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(ok=True, time=datetime.utcnow())

@api_router.get("/history", response_model=HistoryResponse)
def history(
    limit: int = Query(100, ge=1, le=500),
    cursor: Optional[datetime] = Query(None, description="ISO8601 (이 시각 이전 데이터)")
    , db: Session = Depends(get_db),
):
    q = db.query(TradingHistory)
    if cursor is not None:
        q = q.filter(TradingHistory.timestamp < cursor)
    rows = (q.order_by(TradingHistory.timestamp.desc())
              .limit(limit)
              .all())
    rows = list(reversed(rows))  # 시간 오름차순으로 반환

    items = [_to_signal(TradingHistoryOut.model_validate(r)) for r in rows]
    next_cursor = rows[0].timestamp if rows else None  # 다음 페이지 커서(가장 앞의 시각)
    return HistoryResponse(items=items, next_cursor=next_cursor)

@api_router.get("/latest", response_model=LatestResponse)
def latest(db: Session = Depends(get_db)):
    row = (db.query(TradingHistory)
             .order_by(TradingHistory.timestamp.desc())
             .limit(1)
             .first())
    if not row:
        return LatestResponse(last_price=0.0, last_signal=None)
    dto = TradingHistoryOut.model_validate(row)
    sig = _to_signal(dto)
    return LatestResponse(last_price=float(sig.price), last_signal=sig)


# --- NEW: /reflections ---
@api_router.get("/reflections", response_model=ReflectionsResponse)
def reflections(
    limit: int = Query(100, ge=1, le=500),
    cursor: Optional[datetime] = Query(None, description="ISO8601 (이 시각 이전 데이터)"),
    trading_id: Optional[int] = Query(None, description="특정 history id에 대한 reflection만"),
    db: Session = Depends(get_db),
):
    q = db.query(TradingReflection)
    if trading_id is not None:
        q = q.filter(TradingReflection.trading_id == trading_id)
    if cursor is not None:
        q = q.filter(TradingReflection.reflection_date < cursor)

    rows = (q.order_by(TradingReflection.reflection_date.desc())
              .limit(limit)
              .all())
    rows = list(reversed(rows))  # 시간 오름차순 반환

    items = [TradingReflectionOut.model_validate(r) for r in rows]
    next_cursor = rows[0].reflection_date if rows else None
    return ReflectionsResponse(items=items, next_cursor=next_cursor)



# --- WebSocket ---
@api_router.websocket("/ws/updates")
async def ws_updates(ws: WebSocket):
    await ws.accept()
    subscribers.add(ws)

    # ✅ 접속 즉시 부트스트랩 N건 전송 (예: 120건)
    try:
        with SessionLocal() as db:
            rows = (db.query(TradingHistory)
                      .order_by(TradingHistory.timestamp.desc())
                      .limit(120)
                      .all())
        rows = list(reversed(rows))  # 시간 오름차순
        items = [
            {
                "id": dto.id,
                "ts": dto.timestamp,
                "ticker": "BTC/KRW",
                "price": dto.btc_krw_price,
                "type": (dto.decision or "").upper() if (dto.decision or "").upper() in {"BUY","SELL","HOLD","ALERT"} else "HOLD",
                "confidence": dto.percentage,
                "reason": dto.reason,
            }
            for dto in (TradingHistoryOut.model_validate(r) for r in rows)
        ]
        await ws.send_json({"event": "bootstrap", "data": items})
    except Exception as e:
        # bootstrap 실패해도 연결은 유지
        print("[ws bootstrap] error:", e)
        
    try:
        with SessionLocal() as db:
            rws = (db.query(TradingReflection)
                     .order_by(TradingReflection.reflection_date.desc())
                     .limit(120)
                     .all())
        rws = list(reversed(rws))
        ritems = [TradingReflectionOut.model_validate(r) for r in rws]
        await ws.send_json({"event": "bootstrap_reflections", "data": [i.model_dump() for i in ritems]})
    except Exception as e:
        print("[ws bootstrap_reflections] error:", e)

    try:
        while True:
            text = await ws.receive_text()
            if text.strip().lower() == "ping":
                await ws.send_json({"event": "pong", "data": None})
    except WebSocketDisconnect:
        subscribers.discard(ws)
    except Exception:
        subscribers.discard(ws)
