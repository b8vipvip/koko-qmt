"""模拟盘、实盘委托和交易审计 ORM 模型。"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class PaperPosition(Base):
    """模拟盘持仓表。"""

    __tablename__ = "paper_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False, default=0)
    available_volume: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False, default=0)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    last_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    market_value: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False, default=0)
    profit: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class PaperTrade(Base):
    """模拟盘成交表。"""

    __tablename__ = "paper_trades"
    __table_args__ = (Index("ix_paper_trades_symbol_trade_time", "symbol", "trade_time"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    trade_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)


class RealTradeOrder(Base):
    """实盘委托记录表。"""

    __tablename__ = "real_trade_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class TradeAuditLog(Base):
    """交易审计日志表。"""

    __tablename__ = "trade_audit_logs"
    __table_args__ = (Index("ix_trade_audit_logs_action_symbol_created", "action", "symbol", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    symbol: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
