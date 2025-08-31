# watcher.py (개념 예시)
import asyncio
from sqlalchemy.orm import Session
from db import SessionLocal
from models import TradingHistory
from schemas import TradingHistoryOut
from sqlalchemy import select, desc

async def poll_new_rows_loop(db_factory=SessionLocal, broadcast=None, interval_seconds=5):
    last_id = 0
    while True:
        try:
            with db_factory() as db:  # type: Session
                rows = db.execute(
                    select(TradingHistory)
                    .where(TradingHistory.id > last_id)
                    .order_by(TradingHistory.id.asc())
                ).scalars().all()

                for r in rows:
                    last_id = r.id
                    dto = TradingHistoryOut.model_validate(r).model_dump()
                    # dto에는 open/high/low/close/x(=id 또는 timestamp)를 포함하도록 매핑
                    payload = {
                        "x": dto.get("id"),               # 또는 timestamp/seq
                        "open": dto.get("open"),
                        "high": dto.get("high"),
                        "low":  dto.get("low"),
                        "close":dto.get("close"),
                    }
                    if broadcast:
                        broadcast("history", payload)
        except Exception as e:
            print("[poll_new_rows_loop] error:", e)

        await asyncio.sleep(interval_seconds)
