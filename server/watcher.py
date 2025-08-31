# watcher.py
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import TradingHistory
from schemas import TradingHistoryOut

async def poll_new_rows_loop(db_factory, broadcast, interval_seconds=5, start_from_latest=True, bootstrap_last=50):
    print("[poll] start: interval", interval_seconds)

    # 0) 시작 시 최근 N건 먼저 보내기(선택)
    def _bootstrap():
        with db_factory() as db:  # type: Session
            rows = (db.query(TradingHistory)
                      .order_by(TradingHistory.id.desc())
                      .limit(bootstrap_last)
                      .all())
            return list(reversed(rows))
    try:
        init_rows = await asyncio.to_thread(_bootstrap)
        print(f"[poll] bootstrap send {len(init_rows)} rows")
        for r in init_rows:
            dto = TradingHistoryOut.model_validate(r).model_dump()
            payload = {"x": dto.get("id"), "open": dto.get("open"),
                       "high": dto.get("high"), "low": dto.get("low"),
                       "close": dto.get("close")}
            broadcast("history", payload)
    except Exception as e:
        print("[poll] bootstrap error:", e)

    # 1) last_id 초기화
    def _init_max_id():
        with db_factory() as db:
            row = db.execute(select(TradingHistory.id)
                             .order_by(TradingHistory.id.desc())
                             .limit(1)).first()
            return row[0] if row else 0
    last_id = await asyncio.to_thread(_init_max_id) if start_from_latest else 0
    print("[poll] initialized last_id =", last_id)

    # 2) 루프
    while True:
        try:
            def _fetch_since(since_id: int):
                with db_factory() as db:
                    return (db.query(TradingHistory)
                              .filter(TradingHistory.id > since_id)
                              .order_by(TradingHistory.id.asc())
                              .all())
            rows = await asyncio.to_thread(_fetch_since, last_id)
            if rows:
                print(f"[poll] new rows {len(rows)} > id>{last_id}")
            for r in rows:
                last_id = max(last_id, r.id)
                dto = TradingHistoryOut.model_validate(r).model_dump()
                payload = {"x": dto.get("id"), "open": dto.get("open"),
                           "high": dto.get("high"), "low": dto.get("low"),
                           "close": dto.get("close")}
                broadcast("history", payload)
        except Exception as e:
            print("[poll] error:", e)

        await asyncio.sleep(interval_seconds)
