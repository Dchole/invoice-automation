from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Numeric, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.config import settings


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(254))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    company: Mapped[Optional[str]] = mapped_column(String(200))
    currency: Mapped[str] = mapped_column(String(3), default=settings.default_currency)
    default_rate: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    payment_terms: Mapped[int] = mapped_column(
        Integer, default=settings.default_payment_terms
    )
    status: Mapped[str] = mapped_column(String(20), default="active")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    sessions = relationship("Session", back_populates="client", lazy="selectin")
    invoices = relationship("Invoice", back_populates="client", lazy="selectin")

    @property
    def session_count(self) -> int:
        return len(self.sessions)

    @property
    def invoice_count(self) -> int:
        return len(self.invoices)
