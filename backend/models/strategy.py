"""策略信号和分析结果 ORM 模型。"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class StrategySignal(Base):
    """策略信号表。"""

    __tablename__ = "strategy_signals"
    __table_args__ = (Index("ix_strategy_signals_strategy_symbol_date", "strategy_name", "symbol", "signal_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    strategy_name: Mapped[str] = mapped_column(String(64), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    signal_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    score: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    signal_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class LimitUpAnalysis(Base):
    """打板分析结果表。"""

    __tablename__ = "limit_up_analysis"
    __table_args__ = (Index("ix_limit_up_analysis_symbol_trade_date", "symbol", "trade_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    score: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class FuturesArbitrageSignal(Base):
    """期货套利信号表。"""

    __tablename__ = "futures_arbitrage_signals"
    __table_args__ = (Index("ix_futures_arbitrage_contracts_time", "main_contract", "hedge_contract", "signal_time"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    main_contract: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    hedge_contract: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    spread: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    signal_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
