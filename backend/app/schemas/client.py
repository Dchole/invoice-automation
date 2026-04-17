from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

from app.config import settings


class ClientBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    currency: str = settings.default_currency
    default_rate: Optional[float] = None
    payment_terms: int = settings.default_payment_terms
    notes: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    currency: Optional[str] = None
    default_rate: Optional[float] = None
    payment_terms: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ClientRead(ClientBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
