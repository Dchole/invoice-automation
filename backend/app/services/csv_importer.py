from __future__ import annotations
import csv
import io
from datetime import datetime, date, time
from typing import Optional
from sqlalchemy.orm import Session as DbSession

from app.models.client import Client
from app.models.session import Session


def _clean_rate(val: str) -> Optional[float]:
    if not val:
        return None
    s = val.strip().replace("$", "").replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def _parse_duration(val: str, start_time=None, end_time=None) -> Optional[int]:
    if val:
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


def _parse_date(val: str) -> Optional[date]:
    if not val or not val.strip():
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(val.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_time(val: str) -> Optional[time]:
    if not val or not val.strip():
        return None
    for fmt in ("%H:%M", "%I:%M %p", "%H:%M:%S"):
        try:
            return datetime.strptime(val.strip(), fmt).time()
        except ValueError:
            continue
    return None


class ImportResult:
    def __init__(self):
        self.clients_created: int = 0
        self.sessions_created: int = 0
        self.errors: list[str] = []
        self.warnings: list[str] = []


def import_csv(db: DbSession, file_content: str) -> ImportResult:
    result = ImportResult()
    client_cache: dict[str, Client] = {}

    for existing in db.query(Client).all():
        client_cache[existing.name.lower()] = existing

    reader = csv.reader(io.StringIO(file_content))
    rows = list(reader)
    if not rows:
        result.errors.append("CSV file is empty")
        return result

    headers = [h.strip().lower() for h in rows[0]]
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
        elif "status" in h:
            col_map.setdefault("status", i)

    if "client" not in col_map:
        result.errors.append("No client/name column found in CSV")
        return result

    for row_idx, vals in enumerate(rows[1:], start=2):
        if not vals or all(not v.strip() for v in vals):
            continue

        client_name = (
            vals[col_map["client"]].strip() if col_map["client"] < len(vals) else ""
        )
        if not client_name:
            continue

        if client_name.lower() not in client_cache:
            rate = (
                _clean_rate(vals[col_map["rate"]])
                if "rate" in col_map and col_map["rate"] < len(vals)
                else None
            )
            client = Client(name=client_name, default_rate=rate)
            db.add(client)
            db.flush()
            client_cache[client_name.lower()] = client
            result.clients_created += 1

        client = client_cache[client_name.lower()]

        session_date = (
            _parse_date(vals[col_map["date"]])
            if "date" in col_map and col_map["date"] < len(vals)
            else None
        )
        if not session_date:
            result.errors.append(f"Row {row_idx}: invalid or missing date")
            continue

        start = (
            _parse_time(vals[col_map["start"]])
            if "start" in col_map and col_map["start"] < len(vals)
            else None
        )
        end = (
            _parse_time(vals[col_map["end"]])
            if "end" in col_map and col_map["end"] < len(vals)
            else None
        )
        duration = _parse_duration(
            (
                vals[col_map["duration"]]
                if "duration" in col_map and col_map["duration"] < len(vals)
                else ""
            ),
            start,
            end,
        )
        if duration is None or duration <= 0:
            result.errors.append(f"Row {row_idx}: cannot determine duration")
            continue

        rate = (
            _clean_rate(vals[col_map["rate"]])
            if "rate" in col_map and col_map["rate"] < len(vals)
            else None
        )
        if rate is None:
            rate = float(client.default_rate) if client.default_rate else None
        if rate is None:
            result.errors.append(f"Row {row_idx}: no rate found")
            continue

        amount = round(duration / 60.0 * rate, 2)
        desc = (
            vals[col_map["description"]].strip()
            if "description" in col_map
            and col_map["description"] < len(vals)
            and vals[col_map["description"]].strip()
            else None
        )
        status = (
            vals[col_map["status"]].strip().lower()
            if "status" in col_map
            and col_map["status"] < len(vals)
            and vals[col_map["status"]].strip()
            else "unbilled"
        )
        if status not in ("unbilled", "invoiced", "paid"):
            status = "unbilled"

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
