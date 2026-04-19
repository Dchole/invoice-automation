from __future__ import annotations
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DbSession
from sqlalchemy import func

from app.database import get_db
from app.models.invoice import Invoice
from app.models.session import Session
from app.models.client import Client
from app.models.reminder import Reminder
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceRead,
    InvoiceUpdate,
    InvoiceGenerate,
)
from app.config import settings
from app.services.invoice_email import build_invoice_email
from app.pagination import paginate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


def _next_invoice_number(db: DbSession) -> str:
    year = date.today().year
    prefix = f"INV-{year}-"
    last = (
        db.query(Invoice)
        .filter(Invoice.invoice_number.like(f"{prefix}%"))
        .order_by(Invoice.invoice_number.desc())
        .first()
    )
    if last:
        seq = int(last.invoice_number.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


def _schedule_reminders(db: DbSession, invoice: Invoice):
    """Schedule reminders relative to issue_date (when invoice is sent), not due_date."""
    for i, days in enumerate(settings.reminder_days):
        reminder_types = ["friendly", "due", "overdue", "escalation"]
        r = Reminder(
            invoice_id=invoice.id,
            type=reminder_types[i] if i < len(reminder_types) else "escalation",
            scheduled_date=invoice.issue_date + timedelta(days=days),
            status="pending",
        )
        db.add(r)


@router.get("")
def list_invoices(
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: DbSession = Depends(get_db),
):
    q = db.query(Invoice)
    if client_id:
        q = q.filter(Invoice.client_id == client_id)
    if status:
        q = q.filter(Invoice.status == status)
    return paginate(q.order_by(Invoice.issue_date.desc()), page, per_page)


@router.post("", response_model=InvoiceRead, status_code=201)
def create_invoice(data: InvoiceCreate, db: DbSession = Depends(get_db)):
    client = db.get(Client, data.client_id)
    if not client:
        raise HTTPException(404, "Client not found")

    sessions = []
    if data.session_ids:
        sessions = (
            db.query(Session)
            .filter(
                Session.id.in_(data.session_ids),
                Session.client_id == data.client_id,
                Session.status == "unbilled",
            )
            .all()
        )
        if len(sessions) != len(data.session_ids):
            raise HTTPException(400, "Some sessions not found or already invoiced")

    issue = data.issue_date or date.today()
    due = data.due_date or (issue + timedelta(days=client.payment_terms))
    currency = data.currency or client.currency

    subtotal = sum(float(s.amount) for s in sessions) if sessions else 0
    tax_amount = round(subtotal * (data.tax_rate / 100), 2)
    total = round(subtotal + tax_amount, 2)

    invoice = Invoice(
        invoice_number=_next_invoice_number(db),
        client_id=data.client_id,
        issue_date=issue,
        due_date=due,
        subtotal=subtotal,
        tax_rate=data.tax_rate,
        tax_amount=tax_amount,
        total=total,
        currency=currency,
        status="draft",
    )
    db.add(invoice)
    db.flush()

    for s in sessions:
        s.invoice_id = invoice.id
        s.status = "invoiced"

    _schedule_reminders(db, invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@router.post("/generate", response_model=List[InvoiceRead])
def generate_invoices(data: InvoiceGenerate, db: DbSession = Depends(get_db)):
    """Auto-generate invoices for all unbilled sessions, grouped by client."""
    q = db.query(Session).filter(Session.status == "unbilled")
    if data.client_id:
        q = q.filter(Session.client_id == data.client_id)
    unbilled = q.all()

    if not unbilled:
        raise HTTPException(400, "No unbilled sessions found")

    by_client: dict[int, List[Session]] = {}
    for s in unbilled:
        by_client.setdefault(s.client_id, []).append(s)

    invoices = []
    for cid, sessions in by_client.items():
        client = db.get(Client, cid)
        if not client:
            continue
        issue = date.today()
        due = issue + timedelta(days=client.payment_terms or settings.default_payment_terms)
        subtotal = sum(float(s.amount) for s in sessions)
        tax_amount = round(subtotal * (data.tax_rate / 100), 2)
        total = round(subtotal + tax_amount, 2)

        inv = Invoice(
            invoice_number=_next_invoice_number(db),
            client_id=cid,
            issue_date=issue,
            due_date=due,
            subtotal=subtotal,
            tax_rate=data.tax_rate,
            tax_amount=tax_amount,
            total=total,
            currency=client.currency or "CAD",
            status="draft",
        )
        db.add(inv)
        db.flush()

        for s in sessions:
            s.invoice_id = inv.id
            s.status = "invoiced"

        _schedule_reminders(db, inv)
        invoices.append(inv)

    db.commit()
    for inv in invoices:
        db.refresh(inv)
    return invoices


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(invoice_id: int, db: DbSession = Depends(get_db)):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(404, "Invoice not found")
    return inv


@router.put("/{invoice_id}", response_model=InvoiceRead)
def update_invoice(
    invoice_id: int, data: InvoiceUpdate, db: DbSession = Depends(get_db)
):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(404, "Invoice not found")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(inv, key, val)
    db.commit()
    db.refresh(inv)
    return inv


@router.post("/{invoice_id}/send", response_model=InvoiceRead)
def send_invoice(invoice_id: int, db: DbSession = Depends(get_db)):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(404, "Invoice not found")

    client = db.get(Client, inv.client_id)
    if not client:
        raise HTTPException(404, "Client not found")

    # Build line items from sessions
    sessions = db.query(Session).filter(Session.invoice_id == inv.id).all()
    line_items = [
        {
            "date": str(s.date),
            "description": s.description,
            "duration": s.duration_minutes,
            "rate": float(s.hourly_rate),
            "amount": float(s.amount),
        }
        for s in sessions
    ]

    subject, html, plain = build_invoice_email(
        invoice_number=inv.invoice_number,
        client_name=client.name,
        issue_date=inv.issue_date,
        due_date=inv.due_date,
        currency=inv.currency,
        subtotal=float(inv.subtotal),
        tax_rate=float(inv.tax_rate),
        tax_amount=float(inv.tax_amount),
        total=float(inv.total),
        amount_paid=float(inv.amount_paid),
        line_items=line_items,
        notes=inv.notes,
    )

    if client.email:
        if settings.mock_email:
            logger.info(f"[MOCK EMAIL] Invoice {inv.invoice_number} to {client.email}")
        else:
            msg = MIMEMultipart("alternative")
            msg["From"] = settings.smtp_from
            msg["To"] = client.email
            msg["Subject"] = subject
            msg.attach(MIMEText(plain, "plain"))
            msg.attach(MIMEText(html, "html"))
            try:
                with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                    server.starttls()
                    server.login(settings.smtp_user, settings.smtp_password)
                    server.send_message(msg)
                logger.info(f"Invoice {inv.invoice_number} emailed to {client.email}")
            except Exception as e:
                logger.error(f"Failed to email invoice to {client.email}: {e}")
                raise HTTPException(500, f"Failed to send email: {e}")
    else:
        logger.warning(
            f"Client {client.name} has no email — invoice marked sent but not emailed"
        )

    inv.status = "sent"
    inv.sent_at = datetime.utcnow()
    db.commit()
    db.refresh(inv)
    return inv
