import asyncio
from typing import Callable, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from models import TradingHistory, TradingReflection

def poll_new_rows_sync(
    db_factory: Callable[[], Session],
    broadcast: Callable[[Dict[str, Any]], None],
    last_hist_id: int,
    last_refl_id: int,
):
    """동기 트랜잭션 내에서 새 레코드를 찾아 브로드캐스트 큐에 적재"""
    with db_factory() as db:
        # 최신 id
        hist_max = db.execute(select(func.max(TradingHistory.id))).scalar() or 0
        refl_max = db.execute(select(func.max(TradingReflection.id))).scalar() or 0

        # 새 history
        if hist_max > last_hist_id:
            rows = db.execute(
                select(TradingHistory)
                .where(TradingHistory.id > last_hist_id)
                .order_by(TradingHistory.id.asc())
            ).scalars().all()
            for r in rows:
                broadcast({
                    "event": "history",
                    "data": {
                        "id": r.id,
                        "timestamp": r.timestamp.isoformat(),
                        "decision": r.decision,
                        "percentage": r.percentage,
                        "reason": r.reason,
                        "btc_balance": r.btc_balance,
                        "krw_balance": r.krw_balance,
                        "btc_avg_buy_price": r.btc_avg_buy_price,
                        "btc_krw_price": r.btc_krw_price,
                    },
                })
            last_hist_id = hist_max

        # 새 reflection
        if refl_max > last_refl_id:
            rows = db.execute(
                select(TradingReflection)
                .where(TradingReflection.id > last_refl_id)
                .order_by(TradingReflection.id.asc())
            ).scalars().all()
            for r in rows:
                broadcast({
                    "event": "reflection",
                    "data": {
                        "id": r.id,
                        "trading_id": r.trading_id,
                        "reflection_date": r.reflection_date.isoformat(),
                        "market_condition": r.market_condition,
                        "decision_analysis": r.decision_analysis,
                        "improvement_points": r.improvement_points,
                        "success_rate": r.success_rate,
                        "learning_points": r.learning_points,
                    },
                })
            last_refl_id = refl_max

    return last_hist_id, last_refl_id

async def poll_new_rows_loop(
    db_factory: Callable[[], Session],
    broadcast: Callable[[Dict[str, Any]], None],
    interval_seconds: int = 5,
):
    """주기적으로 SQLite를 폴링하여 신규 레코드가 있으면 브로드캐스트"""
    last_hist_id = 0
    last_refl_id = 0

    while True:
        try:
            last_hist_id, last_refl_id = poll_new_rows_sync(
                db_factory=db_factory,
                broadcast=broadcast,
                last_hist_id=last_hist_id,
                last_refl_id=last_refl_id,
            )
        except Exception as e:
            print(f"[watcher] error: {e}")
        await asyncio.sleep(interval_seconds)
