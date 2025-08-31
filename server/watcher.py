# watcher.py
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import TradingHistory
from schemas import TradingHistoryOut

async def poll_new_rows_loop(db_factory, broadcast, interval_seconds=5, start_from_latest=True):
    print("[poll] start: interval", interval_seconds)
    last_id = 0

    # 시작 시점에 현재 최대 id에서 시작(과거 전체를 다시 안 보냄)
    if start_from_latest:
        def _init_max_id():
            with db_factory() as db:  # type: Session
                row = db.execute(select(TradingHistory.id).order_by(TradingHistory.id.desc()).limit(1)).first()
                return row[0] if row else 0
        last_id = await asyncio.to_thread(_init_max_id)
        print("[poll] initialized last_id =", last_id)

    while True:
        try:
            def _fetch_since(since_id: int):
                with db_factory() as db:  # type: Session
                    rows = (db.query(TradingHistory)
                              .filter(TradingHistory.id > since_id)
                              .order_by(TradingHistory.id.asc())
                              .all())
                    return rows

            rows = await asyncio.to_thread(_fetch_since, last_id)
            if rows:
                print(f"[poll] new rows: {len(rows)} (from id>{last_id})")

            for r in rows:
                last_id = max(last_id, r.id)
                dto = TradingHistoryOut.model_validate(r).model_dump()

                payload = {
                    "x": dto.get("id"),          # 또는 timestamp/seq
                    "open": dto.get("open"),
                    "high": dto.get("high"),
                    "low":  dto.get("low"),
                    "close":dto.get("close"),
                }
                # 큐에 적재 → ws_writer가 정규화/송신
                broadcast("history", payload)
        except Exception as e:
            print("[poll] error:", e)

        await asyncio.sleep(interval_seconds)
