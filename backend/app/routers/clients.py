from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DbSession

from app.database import get_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=List[ClientRead])
def list_clients(status: Optional[str] = None, db: DbSession = Depends(get_db)):
    q = db.query(Client)
    if status:
        q = q.filter(Client.status == status)
    return q.order_by(Client.name).all()


@router.post("", response_model=ClientRead, status_code=201)
def create_client(data: ClientCreate, db: DbSession = Depends(get_db)):
    client = Client(**data.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: int, db: DbSession = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    return client


@router.put("/{client_id}", response_model=ClientRead)
def update_client(client_id: int, data: ClientUpdate, db: DbSession = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    for key, val in data.model_dump(exclude_unset=True).items():
        setattr(client, key, val)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: int, db: DbSession = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    db.delete(client)
    db.commit()
