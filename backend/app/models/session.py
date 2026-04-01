from __future__ import annotations
from datetime import datetime, date, time
from typing import Optional
from sqlalchemy import String, Text, Numeric, Integer, Date, Time, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[Optional[time]] = mapped_column(Time)
    end_time: Mapped[Optional[time]] = mapped_column(Time)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    hourly_rate: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="unbilled")
    invoice_id: Mapped[Optional[int]] = mapped_column(ForeignKey("invoices.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="sessions")
    invoice = relationship("Invoice", back_populates="sessions")
