from __future__ import annotations
import csv
import io
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.client import Client
from app.models.session import Session as SessionModel
from app.services.excel_importer import import_excel

router = APIRouter(prefix="/api/import", tags=["import/export"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


@router.post("/excel")
def upload_excel(file: UploadFile = File(...), db: DbSession = Depends(get_db)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Only .xlsx or .xls files are supported")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_DIR / f"import_{file.filename}"
    try:
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
        result = import_excel(db, str(dest))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Failed to process file: {e}")
    return {
        "clients_created": result.clients_created,
        "sessions_created": result.sessions_created,
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
