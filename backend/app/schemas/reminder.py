from __future__ import annotations
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


class ReminderRead(BaseModel):
    id: int
    invoice_id: int
    type: str
    scheduled_date: date
    sent_at: Optional[datetime]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
