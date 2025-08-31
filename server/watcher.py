# server/watcher.py
import asyncio
from sqlalchemy.orm import Session
from models import TradingHistory
from schemas import TradingHistoryOut
from datetime import datetime

def _to_signal_dto(dto: TradingHistoryOut):
    # DB 필드 → RN 요구 스키마 매핑
    t = dto
    typ = (t.decision or "").upper()  # "BUY"/"SELL"/"HOLD" 가정
    return {
        "id": t.id,
        "ts": t.timestamp,             # pydantic json()에서 ISO로 직렬화
        "ticker": "BTC/KRW",
        "price": t.btc_krw_price,
        "type": typ if typ in {"BUY", "SELL", "HOLD", "ALERT"} else "HOLD",
        "confidence": t.percentage,
        "reason": t.reason,
    }

async def poll_new_rows_loop(db_factory, broadcast, interval_seconds=5, start_from_latest=True, bootstrap_last=50):
    print("[poll] start: interval", interval_seconds)

    # 0) 시작 시 최근 N건 bootstrap
    def _bootstrap():
        with db_factory() as db:  # type: Session
            rows = (db.query(TradingHistory)
                      .order_by(TradingHistory.id.desc())
                      .limit(bootstrap_last)
                      .all())
            return list(reversed(rows))
    init_rows = await asyncio.to_thread(_bootstrap)
    from schemas import TradingHistoryOut
    boots = [TradingHistoryOut.model_validate(r) for r in init_rows]
    payload = [_to_signal_dto(b) for b in boots]
    broadcast("bootstrap", payload)

    # 1) 기준 id
    def _init_max_id():
        with db_factory() as db:
            row = (db.query(TradingHistory.id)
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
            for r in rows:
                last_id = max(last_id, r.id)
                dto = TradingHistoryOut.model_validate(r)
                broadcast("signal", _to_signal_dto(dto))
        except Exception as e:
            print("[poll] error:", e)
        await asyncio.sleep(interval_seconds)
