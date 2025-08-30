from pydantic import BaseModel
from datetime import datetime

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
