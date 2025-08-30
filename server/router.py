from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from typing import List

from db import get_db
from models import TradingHistory, TradingReflection
from schemas import TradingHistoryOut, TradingReflectionOut
from broadcast import subscribers

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

# WebSocket 라우트
@api_router.websocket("/ws/updates")
async def ws_updates(ws: WebSocket):
    await ws.accept()
    subscribers.add(ws)
    try:
        while True:
            await ws.receive_text()  # 클라 ping용
    except WebSocketDisconnect:
        subscribers.discard(ws)
