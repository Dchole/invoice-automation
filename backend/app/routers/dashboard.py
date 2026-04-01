from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.services.cashflow_forecast import (
    get_summary,
    get_aging,
    get_client_scores,
    get_cashflow_forecast,
)
from app.schemas.dashboard import DashboardSummary, AgingBucket, ClientScore, CashFlowPoint
from app.currency import convert
from app.models.invoice import Invoice
from app.models.client import Client

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _convert_summary(data: dict, display_currency: str, db: DbSession) -> dict:
    """Convert all monetary amounts in summary to display_currency."""
    # We need to compute converted amounts from individual invoices since
    # the aggregate sums mix currencies
    from sqlalchemy import func
    from app.models.payment import Payment
    from app.models.session import Session
    from datetime import date

    today = date.today()
    month_start = today.replace(day=1)
    if month_start.month == 1:
        last_month_start = month_start.replace(year=month_start.year - 1, month=12)
    else:
        last_month_start = month_start.replace(month=month_start.month - 1)
    quarter_month = ((today.month - 1) // 3) * 3 + 1
    quarter_start = today.replace(month=quarter_month, day=1)

    dc = display_currency.upper()

    # Outstanding (sent + overdue)
    total_outstanding = 0.0
    total_overdue = 0.0
    for inv in db.query(Invoice).filter(Invoice.status.in_(["sent", "overdue", "viewed"])).all():
        balance = float(inv.total) - float(inv.amount_paid)
        total_outstanding += convert(balance, inv.currency, dc)
        if inv.status == "overdue":
            total_overdue += convert(balance, inv.currency, dc)

    # Unbilled
    unbilled_amount = 0.0
    for s in db.query(Session).filter(Session.status == "unbilled").all():
        client = db.get(Client, s.client_id)
        curr = client.currency if client else "CAD"
        unbilled_amount += convert(float(s.amount), curr, dc)

    # Revenue this month
    revenue_this_month = 0.0
    revenue_last_month = 0.0
    revenue_this_quarter = 0.0
    for p in db.query(Payment).all():
        inv = db.get(Invoice, p.invoice_id)
        curr = inv.currency if inv else "CAD"
        converted = convert(float(p.amount), curr, dc)
        if p.payment_date >= month_start:
            revenue_this_month += converted
        if last_month_start <= p.payment_date < month_start:
            revenue_last_month += converted
        if p.payment_date >= quarter_start:
            revenue_this_quarter += converted

    data["total_outstanding"] = round(total_outstanding, 2)
    data["total_overdue"] = round(total_overdue, 2)
    data["unbilled_amount"] = round(unbilled_amount, 2)
    data["revenue_this_month"] = round(revenue_this_month, 2)
    data["revenue_last_month"] = round(revenue_last_month, 2)
    data["revenue_this_quarter"] = round(revenue_this_quarter, 2)
    data["display_currency"] = dc
    return data


@router.get("/summary")
def dashboard_summary(display_currency: Optional[str] = None, db: DbSession = Depends(get_db)):
    data = get_summary(db)
    if display_currency:
        data = _convert_summary(data, display_currency, db)
    else:
        data["display_currency"] = None
    return data


@router.get("/aging")
def dashboard_aging(display_currency: Optional[str] = None, db: DbSession = Depends(get_db)):
    if not display_currency:
        return get_aging(db)

    # Compute aging with currency conversion
    from datetime import date
    dc = display_currency.upper()
    today = date.today()
    buckets = {"current": 0.0, "days_30": 0.0, "days_60": 0.0, "days_90_plus": 0.0}

    for inv in db.query(Invoice).filter(Invoice.status.in_(["sent", "overdue", "viewed"])).all():
        balance = convert(float(inv.total) - float(inv.amount_paid), inv.currency, dc)
        days_old = (today - inv.due_date).days
        if days_old <= 0:
            buckets["current"] += balance
        elif days_old <= 30:
            buckets["days_30"] += balance
        elif days_old <= 60:
            buckets["days_60"] += balance
        else:
            buckets["days_90_plus"] += balance

    return {k: round(v, 2) for k, v in buckets.items()}


@router.get("/client-scores")
def dashboard_client_scores(display_currency: Optional[str] = None, db: DbSession = Depends(get_db)):
    scores = get_client_scores(db)
    if not display_currency:
        return scores

    dc = display_currency.upper()
    for s in scores:
        client = db.query(Client).filter(Client.id == s["client_id"]).first()
        curr = client.currency if client else "CAD"
        s["outstanding_balance"] = convert(s["outstanding_balance"], curr, dc)
        s["total_invoiced"] = convert(s["total_invoiced"], curr, dc)
        s["total_paid"] = convert(s["total_paid"], curr, dc)
    return scores


@router.get("/cashflow", response_model=List[CashFlowPoint])
def dashboard_cashflow(days: int = 90, db: DbSession = Depends(get_db)):
    return get_cashflow_forecast(db, days)
