# server/router.py
from __future__ import annotations
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from db import get_db
from models import TradingHistory
from schemas import (
    TradingHistoryOut, SignalOut, HistoryResponse, LatestResponse, HealthResponse
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

# --- WebSocket ---
@api_router.websocket("/ws/updates")
async def ws_updates(ws: WebSocket):
    await ws.accept()
    subscribers.add(ws)
    try:
        while True:
            text = await ws.receive_text()
            if text.strip().lower() == "ping":
                await ws.send_json({"event": "pong", "data": None})
    except WebSocketDisconnect:
        subscribers.discard(ws)
    except Exception:
        subscribers.discard(ws)
