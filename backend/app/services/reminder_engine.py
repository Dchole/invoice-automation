from __future__ import annotations
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session as DbSession

from app.models.reminder import Reminder
from app.models.invoice import Invoice
from app.models.client import Client
from app.config import settings

logger = logging.getLogger(__name__)


REMINDER_TYPES = ["friendly", "due", "overdue", "escalation"]


def schedule_reminders(db: DbSession, invoice: Invoice):
    """Schedule reminders relative to issue_date for an invoice."""
    for i, days in enumerate(settings.reminder_days):
        r = Reminder(
            invoice_id=invoice.id,
            type=REMINDER_TYPES[i] if i < len(REMINDER_TYPES) else "escalation",
            scheduled_date=invoice.issue_date + timedelta(days=days),
            status="pending",
        )
        db.add(r)


def schedule_reminders_for_unpaid(db: DbSession) -> int:
    """Schedule reminders for all unpaid invoices that don't already have reminders."""
    unpaid = (
        db.query(Invoice)
        .filter(Invoice.status.in_(["sent", "overdue", "viewed", "draft"]))
        .all()
    )
    count = 0
    for inv in unpaid:
        existing = db.query(Reminder).filter(Reminder.invoice_id == inv.id).first()
        if not existing:
            schedule_reminders(db, inv)
            count += 1
    return count


REMINDER_SUBJECTS = {
    "friendly": "Friendly reminder: Invoice {inv} is due soon",
    "due": "Payment due: Invoice {inv}",
    "overdue": "Overdue notice: Invoice {inv}",
    "escalation": "Action required: Invoice {inv} is significantly overdue",
}

REMINDER_BODIES = {
    "friendly": (
        "Hi {client},\n\n"
        "Just a friendly reminder that invoice {inv} for {amount} {currency} "
        "is due on {due_date}.\n\n"
        "If you've already sent payment, please disregard this message.\n\n"
        "Thank you,\nInvoiceFlow"
    ),
    "due": (
        "Hi {client},\n\n"
        "This is a reminder that payment for invoice {inv} ({amount} {currency}) "
        "was due on {due_date}.\n\n"
        "Please arrange payment at your earliest convenience.\n\n"
        "Thank you,\nInvoiceFlow"
    ),
    "overdue": (
        "Hi {client},\n\n"
        "Invoice {inv} for {amount} {currency} is now overdue. "
        "The payment was due on {due_date}.\n\n"
        "Please let us know if there are any issues with this invoice.\n\n"
        "Thank you,\nInvoiceFlow"
    ),
    "escalation": (
        "Hi {client},\n\n"
        "We have not yet received payment for invoice {inv} ({amount} {currency}), "
        "which was due on {due_date}. This invoice is now significantly overdue.\n\n"
        "Please contact us immediately to resolve this matter.\n\n"
        "Thank you,\nInvoiceFlow"
    ),
}


def process_due_reminders(db: DbSession) -> list[dict]:
    """Find and send all reminders that are due today or earlier."""
    today = date.today()
    pending = (
        db.query(Reminder)
        .filter(Reminder.status == "pending", Reminder.scheduled_date <= today)
        .all()
    )

    sent = []
    for r in pending:
        invoice = db.get(Invoice, r.invoice_id)
        if not invoice or invoice.status == "paid":
            r.status = "skipped"
            continue

        if settings.mock_email:
            logger.info(
                f"[MOCK EMAIL] Reminder {r.type} for invoice {invoice.invoice_number} "
                f"to client_id={invoice.client_id}"
            )
        else:
            _send_email(invoice, r, db)

        r.status = "sent"
        r.sent_at = datetime.utcnow()
        sent.append(
            {
                "reminder_id": r.id,
                "invoice_number": invoice.invoice_number,
                "type": r.type,
                "client_id": invoice.client_id,
            }
        )

    db.commit()
    return sent


def _send_email(invoice: Invoice, reminder: Reminder, db: DbSession):
    """Send a reminder email via SMTP."""
    client = db.get(Client, invoice.client_id)
    if not client or not client.email:
        logger.warning(f"No email for client_id={invoice.client_id}, skipping send")
        return

    remaining = float(invoice.total) - float(invoice.amount_paid)
    template_vars = {
        "client": client.name,
        "inv": invoice.invoice_number,
        "amount": f"${remaining:,.2f}",
        "currency": invoice.currency,
        "due_date": str(invoice.due_date),
    }

    subject = REMINDER_SUBJECTS.get(reminder.type, "Invoice reminder: {inv}").format(
        **template_vars
    )
    body = REMINDER_BODIES.get(reminder.type, "Please review invoice {inv}.").format(
        **template_vars
    )

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
        logger.info(f"Email sent to {client.email}: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email to {client.email}: {e}")
        raise


def check_overdue_invoices(db: DbSession) -> int:
    """Mark invoices as overdue if past due date and not paid."""
    today = date.today()
    overdue = (
        db.query(Invoice)
        .filter(
            Invoice.due_date < today,
            Invoice.status.in_(["sent", "viewed"]),
        )
        .all()
    )
    for inv in overdue:
        inv.status = "overdue"
    db.commit()
    return len(overdue)
