from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from typing import List

from db import get_db
from models import TradingHistory, TradingReflection
from schemas import TradingHistoryOut, TradingReflectionOut
from broadcast import subscribers, broadcast, sanitize_candle


api_router = APIRouter()

@api_router.get("/health")
def health():
    return {"ok": True}

@api_router.get("/history", response_model=List[TradingHistoryOut])
def list_history(limit: int = 100, db: Session = Depends(get_db)):
    rows = db.execute(
        select(TradingHistory).order_by(desc(TradingHistory.id)).limit(limit)
    ).scalars().all()
    return list(reversed(rows))

@api_router.get("/reflections", response_model=List[TradingReflectionOut])
def list_reflections(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.execute(
        select(TradingReflection).order_by(desc(TradingReflection.id)).limit(limit)
    ).scalars().all()
    return list(reversed(rows))

# WebSocket
@api_router.websocket("/ws/updates")
async def ws_updates(ws: WebSocket):
    await ws.accept()
    subscribers.add(ws)
    try:
        while True:
            _ = await ws.receive_text()  # ping 등 무시
    except WebSocketDisconnect:
        subscribers.discard(ws)

# 예: DB에 새 TradingHistory가 들어온 직후 호출하는 헬퍼
async def on_new_history(db_row) -> None:
    # db_row -> dict 변환 (필드명은 상황에 맞게 매핑)
    raw = {
        "x": db_row.id,                # 또는 timestamp/sequence
        "open": db_row.open,
        "high": db_row.high,
        "low":  db_row.low,
        "close":db_row.close,
    }
    safe = sanitize_candle(raw)
    await broadcast("history", safe)
