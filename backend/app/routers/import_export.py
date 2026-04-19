from __future__ import annotations
import csv
import io
import shutil
from datetime import date
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from openpyxl import Workbook
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.client import Client
from app.models.session import Session as SessionModel
from app.models.reminder import Reminder
from app.services.excel_importer import import_excel
from app.services.csv_importer import import_csv
from app.services.reminder_engine import schedule_reminders_for_unpaid

router = APIRouter(prefix="/api/import", tags=["import/export"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


@router.delete("/reset")
def reset_all_data(db: DbSession = Depends(get_db)):
    """Delete all data from all tables."""
    db.query(Reminder).delete()
    db.query(Payment).delete()
    db.query(SessionModel).delete()
    db.query(Invoice).delete()
    db.query(Client).delete()
    db.commit()
    return {"message": "All data cleared"}


@router.post("/excel")
def upload_excel(file: UploadFile = File(...), db: DbSession = Depends(get_db)):
    safe_filename = Path(file.filename).name
    if not safe_filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Only .xlsx or .xls files are supported")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / f"import_{safe_filename}"
    try:
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
        result = import_excel(db, str(dest))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Failed to process file: {e}")
    reminders_created = schedule_reminders_for_unpaid(db)
    db.commit()
    return {
        "clients_created": result.clients_created,
        "sessions_created": result.sessions_created,
        "invoices_created": result.invoices_created,
        "payments_created": result.payments_created,
        "reminders_created": reminders_created,
        "errors": result.errors,
        "warnings": result.warnings,
    }


@router.post("/csv")
def upload_csv(file: UploadFile = File(...), db: DbSession = Depends(get_db)):
    filename = (file.filename or "").lower()
    if not filename.endswith(".csv"):
        raise HTTPException(400, "Only .csv files are supported")

    try:
        content = file.file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(400, "CSV file must be UTF-8 encoded")
    result = import_csv(db, content)
    reminders_created = schedule_reminders_for_unpaid(db)
    db.commit()
    return {
        "clients_created": result.clients_created,
        "sessions_created": result.sessions_created,
        "reminders_created": reminders_created,
        "errors": result.errors,
        "warnings": result.warnings,
    }


@router.get("/export/backup")
def export_backup():
    db_path = UPLOAD_DIR / "invoices.db"
    if not db_path.exists():
        raise HTTPException(404, "Database not found")
    return FileResponse(
        str(db_path),
        filename="invoices_backup.db",
        media_type="application/octet-stream",
    )


@router.get("/export/invoices-csv")
def export_invoices_csv(db: DbSession = Depends(get_db)):
    """Export all invoices as CSV for accounting software."""
    invoices = db.query(Invoice).order_by(Invoice.issue_date.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Invoice Number",
            "Client",
            "Client Email",
            "Issue Date",
            "Due Date",
            "Subtotal",
            "Tax Rate %",
            "Tax Amount",
            "Total",
            "Amount Paid",
            "Balance",
            "Currency",
            "Status",
            "Sent Date",
            "Paid Date",
        ]
    )
    for inv in invoices:
        client = db.get(Client, inv.client_id)
        balance = float(inv.total) - float(inv.amount_paid)
        writer.writerow(
            [
                inv.invoice_number,
                client.name if client else "",
                client.email if client and client.email else "",
                str(inv.issue_date),
                str(inv.due_date),
                f"{float(inv.subtotal):.2f}",
                f"{float(inv.tax_rate):.2f}",
                f"{float(inv.tax_amount):.2f}",
                f"{float(inv.total):.2f}",
                f"{float(inv.amount_paid):.2f}",
                f"{balance:.2f}",
                inv.currency,
                inv.status,
                str(inv.sent_at or ""),
                str(inv.paid_at or ""),
            ]
        )
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=invoices_export.csv"},
    )


@router.get("/export/payments-csv")
def export_payments_csv(db: DbSession = Depends(get_db)):
    """Export all payments as CSV for accounting software."""
    payments = db.query(Payment).order_by(Payment.payment_date.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Date",
            "Invoice Number",
            "Client",
            "Client Email",
            "Amount",
            "Payment Method",
            "Reference",
            "Notes",
        ]
    )
    for p in payments:
        inv = db.get(Invoice, p.invoice_id)
        client = db.get(Client, inv.client_id) if inv else None
        writer.writerow(
            [
                str(p.payment_date),
                inv.invoice_number if inv else "",
                client.name if client else "",
                client.email if client and client.email else "",
                f"{float(p.amount):.2f}",
                p.payment_method or "",
                p.reference or "",
                p.notes or "",
            ]
        )
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=payments_export.csv"},
    )


@router.get("/export/invoices-excel")
def export_invoices_excel(db: DbSession = Depends(get_db)):
    """Export all invoices as Excel (.xlsx) for accounting software."""
    invoices = db.query(Invoice).order_by(Invoice.issue_date.desc()).all()
    wb = Workbook()
    ws = wb.active
    ws.title = "Invoices"
    ws.append(
        [
            "Invoice Number",
            "Client",
            "Client Email",
            "Issue Date",
            "Due Date",
            "Subtotal",
            "Tax Rate %",
            "Tax Amount",
            "Total",
            "Amount Paid",
            "Balance",
            "Currency",
            "Status",
            "Sent Date",
            "Paid Date",
        ]
    )
    for inv in invoices:
        client = db.get(Client, inv.client_id)
        balance = float(inv.total) - float(inv.amount_paid)
        ws.append(
            [
                inv.invoice_number,
                client.name if client else "",
                client.email if client and client.email else "",
                str(inv.issue_date),
                str(inv.due_date),
                float(inv.subtotal),
                float(inv.tax_rate),
                float(inv.tax_amount),
                float(inv.total),
                float(inv.amount_paid),
                balance,
                inv.currency,
                inv.status,
                str(inv.sent_at or ""),
                str(inv.paid_at or ""),
            ]
        )
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=invoices_export.xlsx"},
    )


@router.get("/export/payments-excel")
def export_payments_excel(db: DbSession = Depends(get_db)):
    """Export all payments as Excel (.xlsx) for accounting software."""
    payments = db.query(Payment).order_by(Payment.payment_date.desc()).all()
    wb = Workbook()
    ws = wb.active
    ws.title = "Payments"
    ws.append(
        [
            "Date",
            "Invoice Number",
            "Client",
            "Client Email",
            "Amount",
            "Payment Method",
            "Reference",
            "Notes",
        ]
    )
    for p in payments:
        inv = db.get(Invoice, p.invoice_id)
        client = db.get(Client, inv.client_id) if inv else None
        ws.append(
            [
                str(p.payment_date),
                inv.invoice_number if inv else "",
                client.name if client else "",
                client.email if client and client.email else "",
                float(p.amount),
                p.payment_method or "",
                p.reference or "",
                p.notes or "",
            ]
        )
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=payments_export.xlsx"},
    )


@router.get("/export/excel")
def export_excel(db: DbSession = Depends(get_db)):
    """Export all data as a single .xlsx workbook that can be re-imported."""
    wb = Workbook()

    # --- Client Summary sheet ---
    ws_clients = wb.active
    ws_clients.title = "Client Summary"
    ws_clients.append(["Client Name", "Email", "Currency", "Rate", "Payment Terms"])
    clients = db.query(Client).order_by(Client.name).all()
    client_map: dict[int, Client] = {}
    for c in clients:
        client_map[c.id] = c
        ws_clients.append(
            [
                c.name,
                c.email or "",
                c.currency,
                float(c.default_rate) if c.default_rate else "",
                c.payment_terms,
            ]
        )

    # --- Invoices sheet ---
    ws_inv = wb.create_sheet("Invoices")
    ws_inv.append(
        [
            "Invoice Number",
            "Client",
            "Client Email",
            "Issue Date",
            "Due Date",
            "Subtotal",
            "Tax Rate %",
            "Tax Amount",
            "Total",
            "Amount Paid",
            "Balance",
            "Currency",
            "Status",
            "Sent Date",
            "Paid Date",
        ]
    )
    invoices = db.query(Invoice).order_by(Invoice.issue_date.desc()).all()
    for inv in invoices:
        client = client_map.get(inv.client_id)
        balance = float(inv.total) - float(inv.amount_paid)
        ws_inv.append(
            [
                inv.invoice_number,
                client.name if client else "",
                client.email if client and client.email else "",
                inv.issue_date,
                inv.due_date,
                float(inv.subtotal),
                float(inv.tax_rate),
                float(inv.tax_amount),
                float(inv.total),
                float(inv.amount_paid),
                round(balance, 2),
                inv.currency,
                inv.status,
                str(inv.sent_at.date()) if inv.sent_at else "",
                str(inv.paid_at.date()) if inv.paid_at else "",
            ]
        )

    # --- Payments sheet ---
    ws_pay = wb.create_sheet("Payments")
    ws_pay.append(
        [
            "Date",
            "Invoice Number",
            "Client",
            "Client Email",
            "Amount",
            "Payment Method",
            "Reference",
            "Notes",
        ]
    )
    payments = db.query(Payment).order_by(Payment.payment_date.desc()).all()
    for p in payments:
        inv = db.get(Invoice, p.invoice_id)
        client = client_map.get(inv.client_id) if inv else None
        ws_pay.append(
            [
                p.payment_date,
                inv.invoice_number if inv else "",
                client.name if client else "",
                client.email if client and client.email else "",
                float(p.amount),
                p.payment_method or "",
                p.reference or "",
                p.notes or "",
            ]
        )

    # --- Sessions sheet ---
    ws_sess = wb.create_sheet("Sessions")
    ws_sess.append(
        [
            "Client",
            "Client Email",
            "Date",
            "Duration",
            "Rate",
            "Amount",
            "Description",
            "Status",
        ]
    )
    sessions = db.query(SessionModel).order_by(SessionModel.date.desc()).all()
    for s in sessions:
        client = client_map.get(s.client_id)
        ws_sess.append(
            [
                client.name if client else "",
                client.email if client and client.email else "",
                s.date,
                s.duration_minutes,
                float(s.hourly_rate) if s.hourly_rate else "",
                float(s.amount) if s.amount else "",
                s.description or "",
                s.status,
            ]
        )

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    today = date.today().isoformat()
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=invoice_automation_export_{today}.xlsx"
        },
    )


@router.get("/export/csv")
def export_csv(db: DbSession = Depends(get_db)):
    """Export all data as a single CSV (multiple sections separated by headers)."""
    output = io.StringIO()
    writer = csv.writer(output)

    # --- Clients ---
    clients = db.query(Client).order_by(Client.name).all()
    client_map: dict[int, Client] = {}
    writer.writerow(["## Clients"])
    writer.writerow(["Client Name", "Email", "Currency", "Rate", "Payment Terms"])
    for c in clients:
        client_map[c.id] = c
        writer.writerow(
            [
                c.name,
                c.email or "",
                c.currency,
                f"{float(c.default_rate):.2f}" if c.default_rate else "",
                c.payment_terms,
            ]
        )

    # --- Invoices ---
    writer.writerow([])
    writer.writerow(["## Invoices"])
    writer.writerow(
        [
            "Invoice Number",
            "Client",
            "Client Email",
            "Issue Date",
            "Due Date",
            "Subtotal",
            "Tax Rate %",
            "Tax Amount",
            "Total",
            "Amount Paid",
            "Balance",
            "Currency",
            "Status",
            "Sent Date",
            "Paid Date",
        ]
    )
    invoices = db.query(Invoice).order_by(Invoice.issue_date.desc()).all()
    for inv in invoices:
        client = client_map.get(inv.client_id)
        balance = float(inv.total) - float(inv.amount_paid)
        writer.writerow(
            [
                inv.invoice_number,
                client.name if client else "",
                client.email if client and client.email else "",
                str(inv.issue_date),
                str(inv.due_date),
                f"{float(inv.subtotal):.2f}",
                f"{float(inv.tax_rate):.2f}",
                f"{float(inv.tax_amount):.2f}",
                f"{float(inv.total):.2f}",
                f"{float(inv.amount_paid):.2f}",
                f"{balance:.2f}",
                inv.currency,
                inv.status,
                str(inv.sent_at or ""),
                str(inv.paid_at or ""),
            ]
        )

    # --- Payments ---
    writer.writerow([])
    writer.writerow(["## Payments"])
    writer.writerow(
        [
            "Date",
            "Invoice Number",
            "Client",
            "Client Email",
            "Amount",
            "Payment Method",
            "Reference",
            "Notes",
        ]
    )
    payments = db.query(Payment).order_by(Payment.payment_date.desc()).all()
    for p in payments:
        inv = db.get(Invoice, p.invoice_id)
        client = client_map.get(inv.client_id) if inv else None
        writer.writerow(
            [
                str(p.payment_date),
                inv.invoice_number if inv else "",
                client.name if client else "",
                client.email if client and client.email else "",
                f"{float(p.amount):.2f}",
                p.payment_method or "",
                p.reference or "",
                p.notes or "",
            ]
        )

    # --- Sessions ---
    writer.writerow([])
    writer.writerow(["## Sessions"])
    writer.writerow(
        [
            "Client",
            "Client Email",
            "Date",
            "Duration",
            "Rate",
            "Amount",
            "Description",
            "Status",
        ]
    )
    sessions = db.query(SessionModel).order_by(SessionModel.date.desc()).all()
    for s in sessions:
        client = client_map.get(s.client_id)
        writer.writerow(
            [
                client.name if client else "",
                client.email if client and client.email else "",
                str(s.date),
                s.duration_minutes,
                f"{float(s.hourly_rate):.2f}" if s.hourly_rate else "",
                f"{float(s.amount):.2f}" if s.amount else "",
                s.description or "",
                s.status,
            ]
        )

    output.seek(0)
    today = date.today().isoformat()
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=invoice_automation_export_{today}.csv"
        },
    )
