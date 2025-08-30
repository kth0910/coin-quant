from sqlalchemy import Column, Integer, Float, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from server.db import Base

class TradingHistory(Base):
    __tablename__ = "trading_history"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False)
    decision = Column(String, nullable=False)          # "buy" | "sell" | "hold"
    percentage = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)

    btc_balance = Column(Float, nullable=False)
    krw_balance = Column(Float, nullable=False)
    btc_avg_buy_price = Column(Float, nullable=False)
    btc_krw_price = Column(Float, nullable=False)

    reflections = relationship("TradingReflection", back_populates="history")

class TradingReflection(Base):
    __tablename__ = "trading_reflection"

    id = Column(Integer, primary_key=True, index=True)
    trading_id = Column(Integer, ForeignKey("trading_history.id"), nullable=False)
    reflection_date = Column(DateTime, nullable=False)

    market_condition = Column(Text, nullable=False)
    decision_analysis = Column(Text, nullable=False)
    improvement_points = Column(Text, nullable=False)
    success_rate = Column(Float, nullable=False)
    learning_points = Column(Text, nullable=False)

    history = relationship("TradingHistory", back_populates="reflections")
