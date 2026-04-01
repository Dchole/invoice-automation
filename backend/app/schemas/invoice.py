from __future__ import annotations
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel


class InvoiceBase(BaseModel):
    client_id: int
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    tax_rate: float = 0
    currency: Optional[str] = None
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    session_ids: List[int] = []


class InvoiceUpdate(BaseModel):
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    tax_rate: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class InvoiceGenerate(BaseModel):
    client_id: Optional[int] = None
    tax_rate: float = 0


class InvoiceRead(BaseModel):
    id: int
    invoice_number: str
    client_id: int
    issue_date: date
    due_date: date
    subtotal: float
    tax_rate: float
    tax_amount: float
    total: float
    amount_paid: float
    currency: str
    status: str
    sent_at: Optional[datetime]
    paid_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
