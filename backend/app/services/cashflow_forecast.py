from __future__ import annotations
from datetime import date, timedelta
from typing import List
from sqlalchemy import func
from sqlalchemy.orm import Session as DbSession

from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.session import Session
from app.models.client import Client


def get_summary(db: DbSession) -> dict:
    today = date.today()
    month_start = today.replace(day=1)
    if month_start.month == 1:
        last_month_start = month_start.replace(year=month_start.year - 1, month=12)
    else:
        last_month_start = month_start.replace(month=month_start.month - 1)
    quarter_month = ((today.month - 1) // 3) * 3 + 1
    quarter_start = today.replace(month=quarter_month, day=1)

    total_outstanding = (
        db.query(func.coalesce(func.sum(Invoice.total - Invoice.amount_paid), 0))
        .filter(Invoice.status.in_(["sent", "overdue", "viewed"]))
        .scalar()
    )

    total_overdue = (
        db.query(func.coalesce(func.sum(Invoice.total - Invoice.amount_paid), 0))
        .filter(Invoice.status == "overdue")
        .scalar()
    )

    unbilled_amount = (
        db.query(func.coalesce(func.sum(Session.amount), 0))
        .filter(Session.status == "unbilled")
        .scalar()
    )

    revenue_this_month = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.payment_date >= month_start)
        .scalar()
    )

    revenue_last_month = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(
            Payment.payment_date >= last_month_start, Payment.payment_date < month_start
        )
        .scalar()
    )

    revenue_this_quarter = (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(Payment.payment_date >= quarter_start)
        .scalar()
    )

    total_clients = (
        db.query(func.count(Client.id)).filter(Client.status == "active").scalar()
    )
    total_invoices = db.query(func.count(Invoice.id)).scalar()
    paid_invoices = (
        db.query(func.count(Invoice.id)).filter(Invoice.status == "paid").scalar()
    )
    overdue_invoices = (
        db.query(func.count(Invoice.id)).filter(Invoice.status == "overdue").scalar()
    )
    draft_invoices = (
        db.query(func.count(Invoice.id)).filter(Invoice.status == "draft").scalar()
    )
    sent_invoices = (
        db.query(func.count(Invoice.id)).filter(Invoice.status == "sent").scalar()
    )
    unbilled_sessions = (
        db.query(func.count(Session.id)).filter(Session.status == "unbilled").scalar()
    )

    # Collection rate: paid invoices / (paid + sent + overdue) × 100
    total_sent_or_resolved = paid_invoices + sent_invoices + overdue_invoices
    collection_rate = (
        round((paid_invoices / total_sent_or_resolved) * 100, 1)
        if total_sent_or_resolved > 0
        else None
    )

    # Average invoicing speed: days from session date to invoice issue_date
    invoiced_sessions = (
        db.query(Session, Invoice.issue_date)
        .join(Invoice, Session.invoice_id == Invoice.id)
        .filter(Session.invoice_id.isnot(None))
        .all()
    )
    if invoiced_sessions:
        total_days = sum(
            max(0, (inv_date - s.date).days)
            for s, inv_date in invoiced_sessions
            if inv_date and s.date
        )
        avg_invoicing_days = (
            round(total_days / len(invoiced_sessions), 1) if invoiced_sessions else None
        )
    else:
        avg_invoicing_days = None

    return {
        "total_outstanding": float(total_outstanding),
        "total_overdue": float(total_overdue),
        "unbilled_amount": float(unbilled_amount),
        "revenue_this_month": float(revenue_this_month),
        "revenue_last_month": float(revenue_last_month),
        "revenue_this_quarter": float(revenue_this_quarter),
        "total_clients": total_clients,
        "total_invoices": total_invoices,
        "paid_invoices": paid_invoices,
        "overdue_invoices": overdue_invoices,
        "draft_invoices": draft_invoices,
        "sent_invoices": sent_invoices,
        "unbilled_sessions": unbilled_sessions,
        "collection_rate": collection_rate,
        "avg_invoicing_days": avg_invoicing_days,
    }


def get_aging(db: DbSession) -> dict:
    today = date.today()
    buckets = {"current": 0.0, "days_30": 0.0, "days_60": 0.0, "days_90_plus": 0.0}

    unpaid = (
        db.query(Invoice)
        .filter(Invoice.status.in_(["sent", "overdue", "viewed"]))
        .all()
    )

    for inv in unpaid:
        balance = float(inv.total) - float(inv.amount_paid)
        days_old = (today - inv.due_date).days
        if days_old <= 0:
            buckets["current"] += balance
        elif days_old <= 30:
            buckets["days_30"] += balance
        elif days_old <= 60:
            buckets["days_60"] += balance
        else:
            buckets["days_90_plus"] += balance

    return buckets


def get_client_scores(db: DbSession) -> List[dict]:
    clients = db.query(Client).filter(Client.status == "active").all()
    scores = []

    for c in clients:
        invoices = db.query(Invoice).filter(Invoice.client_id == c.id).all()
        total_invoiced = sum(float(i.total) for i in invoices)
        total_paid = sum(float(i.amount_paid) for i in invoices)
        outstanding = total_invoiced - total_paid

        paid_invoices = [i for i in invoices if i.paid_at and i.sent_at]
        if paid_invoices:
            avg_days = sum(
                (
                    (i.paid_at.date() - i.issue_date).days
                    if hasattr(i.paid_at, "date")
                    else (i.paid_at - i.issue_date).days
                )
                for i in paid_invoices
            ) / len(paid_invoices)
        else:
            avg_days = None

        last_payment = (
            db.query(func.max(Payment.payment_date))
            .join(Invoice)
            .filter(Invoice.client_id == c.id)
            .scalar()
        )

        overdue_count = sum(1 for i in invoices if i.status == "overdue")
        if overdue_count > 0:
            risk = "at_risk"
        elif avg_days and avg_days > 30:
            risk = "slow_payer"
        else:
            risk = "good"

        scores.append(
            {
                "client_id": c.id,
                "client_name": c.name,
                "outstanding_balance": outstanding,
                "total_invoiced": total_invoiced,
                "total_paid": total_paid,
                "avg_payment_days": round(avg_days, 1) if avg_days else None,
                "last_payment_date": str(last_payment) if last_payment else None,
                "status": risk,
            }
        )

    return scores


def _get_client_avg_payment_days(db: DbSession) -> dict[int, float]:
    """Get average days from issue_date to payment for each client."""
    clients = db.query(Client).all()
    result = {}
    for c in clients:
        paid_invoices = [
            i
            for i in db.query(Invoice)
            .filter(
                Invoice.client_id == c.id,
                Invoice.status == "paid",
                Invoice.paid_at.isnot(None),
                Invoice.issue_date.isnot(None),
            )
            .all()
        ]
        if paid_invoices:
            total_days = sum(
                (
                    (i.paid_at.date() - i.issue_date).days
                    if hasattr(i.paid_at, "date")
                    else (i.paid_at - i.issue_date).days
                )
                for i in paid_invoices
            )
            result[c.id] = total_days / len(paid_invoices)
    return result


def get_cashflow_forecast(db: DbSession, days: int = 90) -> List[dict]:
    today = date.today()

    # Only include actually sent invoices (not drafts)
    unpaid = (
        db.query(Invoice)
        .filter(Invoice.status.in_(["sent", "overdue", "viewed"]))
        .all()
    )

    # Get historical payment speed per client
    client_avg_days = _get_client_avg_payment_days(db)

    daily: dict[str, float] = {}
    for inv in unpaid:
        balance = float(inv.total) - float(inv.amount_paid)
        if balance <= 0:
            continue

        # Predict when payment will arrive based on client history
        avg_days = client_avg_days.get(inv.client_id)
        if avg_days is not None and inv.issue_date:
            # Client has payment history — predict based on their pattern
            expected_date = inv.issue_date + timedelta(days=int(avg_days))
            expected_date = max(expected_date, today)  # Can't be in the past
        else:
            # No history — assume payment on due date
            expected_date = max(inv.due_date, today) if inv.due_date else today

        if (expected_date - today).days > days:
            continue
        key = str(expected_date)
        daily[key] = daily.get(key, 0) + balance

    points = []
    cumulative = 0.0
    for i in range(days + 1):
        d = today + timedelta(days=i)
        key = str(d)
        amt = daily.get(key, 0)
        cumulative += amt
        if amt > 0 or i == 0 or i == days:
            points.append(
                {
                    "date": key,
                    "expected_amount": round(amt, 2),
                    "cumulative": round(cumulative, 2),
                }
            )

    return points
