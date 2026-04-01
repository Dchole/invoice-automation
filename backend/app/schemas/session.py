from __future__ import annotations
from datetime import datetime, date, time
from typing import Optional
from pydantic import BaseModel, model_validator


class SessionBase(BaseModel):
    client_id: int
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    hourly_rate: float
    description: Optional[str] = None

    @model_validator(mode="after")
    def compute_duration(self):
        if self.duration_minutes is None and self.start_time and self.end_time:
            start_dt = datetime.combine(datetime.min, self.start_time)
            end_dt = datetime.combine(datetime.min, self.end_time)
            self.duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
        if self.duration_minutes is None:
            raise ValueError("Either duration_minutes or both start_time and end_time are required")
        return self


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    client_id: Optional[int] = None
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    hourly_rate: Optional[float] = None
    description: Optional[str] = None
    status: Optional[str] = None


class SessionRead(BaseModel):
    id: int
    client_id: int
    date: date
    start_time: Optional[time]
    end_time: Optional[time]
    duration_minutes: int
    hourly_rate: float
    amount: float
    description: Optional[str]
    status: str
    invoice_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}
