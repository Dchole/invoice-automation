from __future__ import annotations
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.models.payment import Payment
from app.models.invoice import Invoice
from app.models.client import Client
from app.models.session import Session
from app.schemas.payment import PaymentCreate, PaymentRead
from app.config import settings
from app.pagination import paginate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.get("")
def list_payments(
    invoice_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: DbSession = Depends(get_db),
):
    q = db.query(Payment)
    if invoice_id:
        q = q.filter(Payment.invoice_id == invoice_id)
    return paginate(q.order_by(Payment.payment_date.desc()), page, per_page)


@router.post("", response_model=PaymentRead, status_code=201)
def create_payment(data: PaymentCreate, db: DbSession = Depends(get_db)):
    invoice = db.get(Invoice, data.invoice_id)
    if not invoice:
        raise HTTPException(404, "Invoice not found")

    payment = Payment(**data.model_dump())
    db.add(payment)

    invoice.amount_paid = float(invoice.amount_paid or 0) + data.amount
    if invoice.amount_paid >= float(invoice.total):
        invoice.status = "paid"
        invoice.paid_at = datetime.utcnow()
        for s in invoice.sessions:
            s.status = "paid"
        for r in invoice.reminders:
            if r.status == "pending":
                r.status = "skipped"

    db.commit()
    db.refresh(payment)

    # Send payment confirmation email
    _send_payment_confirmation(db, invoice, payment)

    return payment


def _send_payment_confirmation(db: DbSession, invoice: Invoice, payment: Payment):
    """Send a confirmation email to the client when a payment is recorded."""
    client = db.get(Client, invoice.client_id)
    if not client or not client.email:
        return

    remaining = float(invoice.total) - float(invoice.amount_paid)
    status_msg = "Your invoice is now paid in full." if remaining <= 0 else f"Remaining balance: ${remaining:,.2f} {invoice.currency}."

    subject = f"Payment received — Invoice {invoice.invoice_number}"
    body = (
        f"Hi {client.name},\n\n"
        f"We've received your payment of ${float(payment.amount):,.2f} for invoice {invoice.invoice_number}.\n\n"
        f"{status_msg}\n\n"
        f"Thank you for your prompt payment!\n\n"
        f"Best regards,\nInvoiceFlow"
    )

    if settings.mock_email:
        logger.info(f"[MOCK EMAIL] Payment confirmation for {invoice.invoice_number} to {client.email}")
        return

    msg = MIMEMultipart()
    msg["From"] = settings.smtp_from
    msg["To"] = client.email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        logger.info(f"Payment confirmation sent to {client.email} for {invoice.invoice_number}")
    except Exception as e:
        logger.error(f"Failed to send payment confirmation: {e}")


@router.post("/bulk", response_model=List[PaymentRead], status_code=201)
def create_payments_bulk(items: List[PaymentCreate], db: DbSession = Depends(get_db)):
    results = []
    for data in items:
        invoice = db.get(Invoice, data.invoice_id)
        if not invoice:
            continue
        payment = Payment(**data.model_dump())
        db.add(payment)
        invoice.amount_paid = float(invoice.amount_paid or 0) + data.amount
        if invoice.amount_paid >= float(invoice.total):
            invoice.status = "paid"
            invoice.paid_at = datetime.utcnow()
            for s in invoice.sessions:
                s.status = "paid"
            for r in invoice.reminders:
                if r.status == "pending":
                    r.status = "skipped"
        results.append(payment)
    db.commit()
    for p in results:
        db.refresh(p)
    return results


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(payment_id: int, db: DbSession = Depends(get_db)):
    p = db.get(Payment, payment_id)
    if not p:
        raise HTTPException(404, "Payment not found")
    return p
