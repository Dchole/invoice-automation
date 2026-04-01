from __future__ import annotations
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


class PaymentBase(BaseModel):
    invoice_id: int
    amount: float
    payment_date: date
    payment_method: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentRead(BaseModel):
    id: int
    invoice_id: int
    amount: float
    payment_date: date
    payment_method: Optional[str]
    reference: Optional[str]
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
