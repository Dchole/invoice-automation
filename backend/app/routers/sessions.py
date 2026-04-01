from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.models.session import Session
from app.schemas.session import SessionCreate, SessionRead, SessionUpdate
from app.pagination import paginate

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("")
def list_sessions(
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: DbSession = Depends(get_db),
):
    q = db.query(Session)
    if client_id:
        q = q.filter(Session.client_id == client_id)
    if status:
        q = q.filter(Session.status == status)
    return paginate(q.order_by(Session.date.desc()), page, per_page)


@router.get("/unbilled", response_model=List[SessionRead])
def list_unbilled(client_id: Optional[int] = None, db: DbSession = Depends(get_db)):
    q = db.query(Session).filter(Session.status == "unbilled")
    if client_id:
        q = q.filter(Session.client_id == client_id)
    return q.order_by(Session.date.desc()).all()


@router.post("", response_model=SessionRead, status_code=201)
def create_session(data: SessionCreate, db: DbSession = Depends(get_db)):
    amount = round(data.duration_minutes / 60.0 * data.hourly_rate, 2)
    session = Session(**data.model_dump(), amount=amount, status="unbilled")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/bulk", response_model=List[SessionRead], status_code=201)
def create_sessions_bulk(items: List[SessionCreate], db: DbSession = Depends(get_db)):
    sessions = []
    for data in items:
        amount = round(data.duration_minutes / 60.0 * data.hourly_rate, 2)
        s = Session(**data.model_dump(), amount=amount, status="unbilled")
        db.add(s)
        sessions.append(s)
    db.commit()
    for s in sessions:
        db.refresh(s)
    return sessions


@router.get("/{session_id}", response_model=SessionRead)
def get_session(session_id: int, db: DbSession = Depends(get_db)):
    s = db.get(Session, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    return s


@router.put("/{session_id}", response_model=SessionRead)
def update_session(session_id: int, data: SessionUpdate, db: DbSession = Depends(get_db)):
    s = db.get(Session, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    updates = data.model_dump(exclude_unset=True)
    for key, val in updates.items():
        setattr(s, key, val)
    if "duration_minutes" in updates or "hourly_rate" in updates:
        s.amount = round(s.duration_minutes / 60.0 * float(s.hourly_rate), 2)
    db.commit()
    db.refresh(s)
    return s


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: int, db: DbSession = Depends(get_db)):
    s = db.get(Session, session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    if s.invoice_id:
        raise HTTPException(400, "Cannot delete an invoiced session")
    db.delete(s)
    db.commit()
