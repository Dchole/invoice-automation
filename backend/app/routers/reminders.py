from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.models.reminder import Reminder
from app.models.invoice import Invoice
from app.schemas.reminder import ReminderRead
from app.services.reminder_engine import _send_email, process_due_reminders, check_overdue_invoices
from app.config import settings
from app.pagination import paginate

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.get("")
def list_reminders(
    invoice_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: DbSession = Depends(get_db),
):
    q = db.query(Reminder)
    if invoice_id:
        q = q.filter(Reminder.invoice_id == invoice_id)
    if status:
        q = q.filter(Reminder.status == status)
    return paginate(q.order_by(Reminder.scheduled_date), page, per_page)


@router.post("/{reminder_id}/send", response_model=ReminderRead)
def send_reminder(reminder_id: int, db: DbSession = Depends(get_db)):
    r = db.get(Reminder, reminder_id)
    if not r:
        raise HTTPException(404, "Reminder not found")
    if r.status != "pending":
        raise HTTPException(400, "Reminder already processed")

    invoice = db.get(Invoice, r.invoice_id)
    if not invoice:
        raise HTTPException(404, "Invoice not found")

    if settings.mock_email:
        logger.info(f"[MOCK EMAIL] Manual send: {r.type} for {invoice.invoice_number}")
    else:
        _send_email(invoice, r, db)

    r.status = "sent"
    r.sent_at = datetime.utcnow()
    db.commit()
    db.refresh(r)
    return r


@router.put("/{reminder_id}/skip", response_model=ReminderRead)
def skip_reminder(reminder_id: int, db: DbSession = Depends(get_db)):
    r = db.get(Reminder, reminder_id)
    if not r:
        raise HTTPException(404, "Reminder not found")
    r.status = "skipped"
    db.commit()
    db.refresh(r)
    return r


@router.post("/run", response_model=dict)
def run_reminders(db: DbSession = Depends(get_db)):
    """Manually trigger the reminder engine (process due reminders + check overdue)."""
    overdue_count = check_overdue_invoices(db)
    sent = process_due_reminders(db)
    return {
        "overdue_marked": overdue_count,
        "reminders_sent": len(sent),
        "details": sent,
    }
