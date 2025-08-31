
# server/schemas.py
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# === Public DTOs ===
class SignalOut(BaseModel):
    id: int
    ts: datetime                    # ISO8601로 직렬화됨
    ticker: str = "BTC/KRW"
    price: float
    type: str                       # BUY | SELL | HOLD | ALERT
    confidence: float
    reason: Optional[str] = None

class HistoryResponse(BaseModel):
    items: List[SignalOut]
    next_cursor: Optional[datetime] = Field(default=None, description="다음 페이지 커서 (ISO8601)")

class LatestResponse(BaseModel):
    last_price: float
    last_signal: Optional[SignalOut] = None

class HealthResponse(BaseModel):
    ok: bool = True
    time: datetime
class TradingHistoryOut(BaseModel):
    id: int
    timestamp: datetime
    decision: str
    percentage: float
    reason: str
    btc_balance: float
    krw_balance: float
    btc_avg_buy_price: float
    btc_krw_price: float
    class Config:
        from_attributes = True

class TradingReflectionOut(BaseModel):
    id: int
    trading_id: int
    reflection_date: datetime
    market_condition: str
    decision_analysis: str
    improvement_points: str
    success_rate: float
    learning_points: str
    class Config:
        from_attributes = True
