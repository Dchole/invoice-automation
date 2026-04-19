from __future__ import annotations
import re
from datetime import datetime, date, time
from typing import Optional
from pathlib import Path
from openpyxl import load_workbook
from sqlalchemy.orm import Session as DbSession

from app.models.client import Client
from app.models.session import Session


def _clean_rate(val) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace("$", "").replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def _parse_duration(val, start_time=None, end_time=None) -> Optional[int]:
    if val is not None:
        try:
            return int(float(val))
        except (ValueError, TypeError):
            pass
    if start_time and end_time:
        if isinstance(start_time, time) and isinstance(end_time, time):
            start_dt = datetime.combine(datetime.min, start_time)
            end_dt = datetime.combine(datetime.min, end_time)
            diff = (end_dt - start_dt).total_seconds() / 60
            if diff > 0:
                return int(diff)
    return None


def _parse_date(val) -> Optional[date]:
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"):
            try:
                return datetime.strptime(val.strip(), fmt).date()
            except ValueError:
                continue
    return None


def _parse_time(val) -> Optional[time]:
    if isinstance(val, time):
        return val
    if isinstance(val, datetime):
        return val.time()
    if isinstance(val, str):
        for fmt in ("%H:%M", "%I:%M %p", "%H:%M:%S"):
            try:
                return datetime.strptime(val.strip(), fmt).time()
            except ValueError:
                continue
    return None


# Map common sheet names to session statuses
STATUS_MAP = {
    "paid": "paid",
    "payment received": "paid",
    "invoiced": "invoiced",
    "invoice sent": "invoiced",
    "sent": "invoiced",
    "unbilled": "unbilled",
    "not invoiced": "unbilled",
    "pending": "unbilled",
    "issues": "unbilled",
    "clients with issues": "unbilled",
}


def _guess_status(sheet_name: str) -> str:
    lower = sheet_name.lower().strip()
    for key, status in STATUS_MAP.items():
        if key in lower:
            return status
    return "unbilled"


class ImportResult:
    def __init__(self):
        self.clients_created: int = 0
        self.sessions_created: int = 0
        self.errors: list[str] = []
        self.warnings: list[str] = []


def _import_client_summary(db: DbSession, wb, client_cache: dict, result: ImportResult):
    """Pre-pass: read Client Summary sheet to populate client details (email, currency, rate)."""
    summary_names = ["client summary", "clients", "client list", "summary"]
    for sheet_name in wb.sheetnames:
        if sheet_name.lower().strip() in summary_names:
            ws = wb[sheet_name]
            rows = list(ws.iter_rows(min_row=1, values_only=False))
            if not rows:
                continue

            headers = [str(c.value or "").strip().lower() for c in rows[0]]
            col = {}
            for i, h in enumerate(headers):
                if "client" in h or "name" in h:
                    col.setdefault("name", i)
                elif "email" in h:
                    col.setdefault("email", i)
                elif "currency" in h:
                    col.setdefault("currency", i)
                elif "rate" in h:
                    col.setdefault("rate", i)
                elif "terms" in h or "payment" in h:
                    col.setdefault("terms", i)

            if "name" not in col:
                continue

            for row in rows[1:]:
                vals = [c.value for c in row]
                name = str(vals[col["name"]] or "").strip()
                if not name:
                    continue

                key = name.lower()
                if key not in client_cache:
                    rate = _clean_rate(vals[col["rate"]]) if "rate" in col else None
                    client = Client(name=name, default_rate=rate)
                    db.add(client)
                    db.flush()
                    client_cache[key] = client
                    result.clients_created += 1

                client = client_cache[key]
                if "email" in col and vals[col["email"]]:
                    email = str(vals[col["email"]]).strip()
                    if email and "@" in email:
                        client.email = email
                if "currency" in col and vals[col["currency"]]:
                    currency = str(vals[col["currency"]]).strip().upper()
                    if currency in ("CAD", "USD", "EUR", "GBP"):
                        client.currency = currency
                if "rate" in col and vals[col["rate"]]:
                    rate = _clean_rate(vals[col["rate"]])
                    if rate:
                        client.default_rate = rate
                if "terms" in col and vals[col["terms"]]:
                    try:
                        client.payment_terms = int(float(vals[col["terms"]]))
                    except (ValueError, TypeError):
                        pass

            db.flush()
            break  # Only process first matching summary sheet


def import_excel(db: DbSession, file_path: str) -> ImportResult:
    result = ImportResult()
    wb = load_workbook(file_path, data_only=True)
    client_cache: dict[str, Client] = {}

    for existing in db.query(Client).all():
        client_cache[existing.name.lower()] = existing

    # Pre-pass: read client summary sheet for emails, currency, rates
    _import_client_summary(db, wb, client_cache, result)

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        status = _guess_status(sheet_name)
        rows = list(ws.iter_rows(min_row=1, values_only=False))
        if not rows:
            continue

        headers = [str(c.value or "").strip().lower() for c in rows[0]]
        header_set = set(headers)

        # Skip sheets that are clearly not session data (payments, invoices, summaries)
        payment_markers = {"payment method", "reference", "invoice number"}
        invoice_markers = {"invoice number", "due date", "tax rate", "tax rate %", "tax amount", "subtotal"}
        summary_markers = {"currency", "payment terms", "email"}
        if payment_markers & header_set and "duration" not in " ".join(headers):
            result.warnings.append(f"Sheet '{sheet_name}': looks like payment data, skipping (import only supports sessions)")
            continue
        if invoice_markers & header_set and "duration" not in " ".join(headers):
            result.warnings.append(f"Sheet '{sheet_name}': looks like invoice data, skipping (import only supports sessions)")
            continue
        if sheet_name.lower().strip() in ("client summary", "clients", "client list", "summary"):
            continue  # Already processed in pre-pass

        col_map = {}
        for i, h in enumerate(headers):
            if "client" in h or "name" in h:
                col_map.setdefault("client", i)
            elif "date" in h and "pay" not in h:
                col_map.setdefault("date", i)
            elif "start" in h:
                col_map.setdefault("start", i)
            elif "end" in h:
                col_map.setdefault("end", i)
            elif "duration" in h or "minutes" in h or "mins" in h:
                col_map.setdefault("duration", i)
            elif "rate" in h:
                col_map.setdefault("rate", i)
            elif "amount" in h or "total" in h or "fee" in h:
                col_map.setdefault("amount", i)
            elif "desc" in h or "note" in h or "service" in h or "topic" in h:
                col_map.setdefault("description", i)

        if "client" not in col_map:
            result.warnings.append(f"Sheet '{sheet_name}': no client column found, skipping")
            continue

        for row_idx, row in enumerate(rows[1:], start=2):
            vals = [c.value for c in row]
            client_name = str(vals[col_map["client"]] or "").strip()
            if not client_name:
                continue

            if client_name.lower() not in client_cache:
                rate = _clean_rate(vals[col_map["rate"]]) if "rate" in col_map else None
                client = Client(name=client_name, default_rate=rate)
                db.add(client)
                db.flush()
                client_cache[client_name.lower()] = client
                result.clients_created += 1

            client = client_cache[client_name.lower()]

            session_date = _parse_date(vals[col_map["date"]]) if "date" in col_map else None
            if not session_date:
                result.errors.append(f"Sheet '{sheet_name}' row {row_idx}: invalid or missing date")
                continue

            start = _parse_time(vals[col_map["start"]]) if "start" in col_map else None
            end = _parse_time(vals[col_map["end"]]) if "end" in col_map else None
            duration = _parse_duration(
                vals[col_map["duration"]] if "duration" in col_map else None,
                start, end,
            )
            if duration is None or duration <= 0:
                result.errors.append(f"Sheet '{sheet_name}' row {row_idx}: cannot determine duration")
                continue

            rate = _clean_rate(vals[col_map["rate"]]) if "rate" in col_map else None
            if rate is None:
                rate = float(client.default_rate) if client.default_rate else None
            if rate is None:
                result.errors.append(f"Sheet '{sheet_name}' row {row_idx}: no rate found")
                continue

            amount = round(duration / 60.0 * rate, 2)
            desc = str(vals[col_map["description"]]) if "description" in col_map and vals[col_map["description"]] else None

            session = Session(
                client_id=client.id,
                date=session_date,
                start_time=start,
                end_time=end,
                duration_minutes=duration,
                hourly_rate=rate,
                amount=amount,
                description=desc,
                status=status,
            )
            db.add(session)
            result.sessions_created += 1

    db.commit()
    return result
