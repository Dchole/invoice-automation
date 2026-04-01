from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_outstanding: float
    total_overdue: float
    unbilled_amount: float
    revenue_this_month: float
    total_clients: int
    total_invoices: int
    paid_invoices: int
    overdue_invoices: int
    draft_invoices: int
    sent_invoices: int
    unbilled_sessions: int
    collection_rate: Optional[float]  # paid / total sent × 100
    avg_invoicing_days: Optional[float]  # avg days from session date to invoice issue_date
    revenue_last_month: float
    revenue_this_quarter: float
    display_currency: Optional[str] = None


class AgingBucket(BaseModel):
    current: float
    days_30: float
    days_60: float
    days_90_plus: float


class ClientScore(BaseModel):
    client_id: int
    client_name: str
    outstanding_balance: float
    total_invoiced: float
    total_paid: float
    avg_payment_days: Optional[float]
    last_payment_date: Optional[str]
    status: str


class CashFlowPoint(BaseModel):
    date: str
    expected_amount: float
    cumulative: float
