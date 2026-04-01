from __future__ import annotations
from datetime import date, timedelta
from typing import Optional
from sqlalchemy.orm import Session as DbSession

from app.models.session import Session
from app.models.invoice import Invoice
from app.models.client import Client
from app.models.reminder import Reminder
from app.config import settings


def _next_invoice_number(db: DbSession) -> str:
    year = date.today().year
    prefix = f"INV-{year}-"
    last = (
        db.query(Invoice)
        .filter(Invoice.invoice_number.like(f"{prefix}%"))
        .order_by(Invoice.invoice_number.desc())
        .first()
    )
    seq = int(last.invoice_number.split("-")[-1]) + 1 if last else 1
    return f"{prefix}{seq:04d}"


def generate_for_client(db: DbSession, client_id: int, tax_rate: float = 0) -> Optional[Invoice]:
    client = db.get(Client, client_id)
    if not client:
        return None

    unbilled = (
        db.query(Session)
        .filter(Session.client_id == client_id, Session.status == "unbilled")
        .all()
    )
    if not unbilled:
        return None

    issue = date.today()
    due = issue + timedelta(days=client.payment_terms)
    subtotal = sum(float(s.amount) for s in unbilled)
    tax_amount = round(subtotal * (tax_rate / 100), 2)
    total = round(subtotal + tax_amount, 2)

    inv = Invoice(
        invoice_number=_next_invoice_number(db),
        client_id=client_id,
        issue_date=issue,
        due_date=due,
        subtotal=subtotal,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        total=total,
        currency=client.currency,
        status="draft",
    )
    db.add(inv)
    db.flush()

    for s in unbilled:
        s.invoice_id = inv.id
        s.status = "invoiced"

    reminder_types = ["friendly", "due", "overdue", "escalation"]
    for i, days in enumerate(settings.reminder_days):
        r = Reminder(
            invoice_id=inv.id,
            type=reminder_types[i] if i < len(reminder_types) else "escalation",
            scheduled_date=due + timedelta(days=days),
            status="pending",
        )
        db.add(r)

    db.commit()
    db.refresh(inv)
    return inv
