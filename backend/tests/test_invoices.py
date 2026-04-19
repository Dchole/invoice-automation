from datetime import date, timedelta


def _setup_client_with_sessions(client, num_sessions=2):
    r = client.post(
        "/api/clients",
        json={
            "name": "Invoice Client",
            "currency": "CAD",
            "default_rate": 150.0,
            "payment_terms": 30,
        },
    )
    cid = r.json()["id"]
    session_ids = []
    for i in range(num_sessions):
        r = client.post(
            "/api/sessions",
            json={
                "client_id": cid,
                "date": f"2025-08-{21 + i:02d}",
                "duration_minutes": 60,
                "hourly_rate": 150.0,
                "description": f"Session {i + 1}",
            },
        )
        session_ids.append(r.json()["id"])
    return cid, session_ids


def test_create_invoice_from_sessions(client):
    cid, sids = _setup_client_with_sessions(client)
    resp = client.post(
        "/api/invoices",
        json={
            "client_id": cid,
            "session_ids": sids,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["subtotal"] == 300.0
    assert data["total"] == 300.0
    assert data["status"] == "draft"
    assert data["invoice_number"].startswith("INV-")
    assert data["currency"] == "CAD"

    # Sessions should now be invoiced
    for sid in sids:
        s = client.get(f"/api/sessions/{sid}").json()
        assert s["status"] == "invoiced"
        assert s["invoice_id"] == data["id"]


def test_create_invoice_with_tax(client):
    cid, sids = _setup_client_with_sessions(client, 1)
    resp = client.post(
        "/api/invoices",
        json={
            "client_id": cid,
            "session_ids": sids,
            "tax_rate": 13.0,
        },
    )
    data = resp.json()
    assert data["subtotal"] == 150.0
    assert data["tax_rate"] == 13.0
    assert data["tax_amount"] == 19.5
    assert data["total"] == 169.5


def test_cannot_invoice_already_invoiced_sessions(client):
    cid, sids = _setup_client_with_sessions(client, 1)
    client.post("/api/invoices", json={"client_id": cid, "session_ids": sids})
    resp = client.post("/api/invoices", json={"client_id": cid, "session_ids": sids})
    assert resp.status_code == 400


def test_generate_invoices_for_all_unbilled(client):
    # Create two clients with unbilled sessions
    r1 = client.post("/api/clients", json={"name": "Client A", "payment_terms": 30})
    r2 = client.post("/api/clients", json={"name": "Client B", "payment_terms": 15})
    cid1, cid2 = r1.json()["id"], r2.json()["id"]

    client.post(
        "/api/sessions",
        json={
            "client_id": cid1,
            "date": "2025-08-21",
            "duration_minutes": 60,
            "hourly_rate": 100.0,
        },
    )
    client.post(
        "/api/sessions",
        json={
            "client_id": cid2,
            "date": "2025-08-22",
            "duration_minutes": 90,
            "hourly_rate": 200.0,
        },
    )

    resp = client.post("/api/invoices/generate", json={})
    assert resp.status_code == 200
    invoices = resp.json()
    assert len(invoices) == 2

    totals = sorted([i["total"] for i in invoices])
    assert totals[0] == 100.0  # 60 min @ $100
    assert totals[1] == 300.0  # 90 min @ $200


def test_generate_invoices_no_unbilled(client):
    resp = client.post("/api/invoices/generate", json={})
    assert resp.status_code == 400


def test_send_invoice(client):
    cid, sids = _setup_client_with_sessions(client, 1)
    r = client.post("/api/invoices", json={"client_id": cid, "session_ids": sids})
    inv_id = r.json()["id"]

    resp = client.post(f"/api/invoices/{inv_id}/send")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "sent"
    assert data["sent_at"] is not None


def test_invoice_creates_reminders(client):
    cid, sids = _setup_client_with_sessions(client, 1)
    r = client.post("/api/invoices", json={"client_id": cid, "session_ids": sids})
    inv_id = r.json()["id"]

    resp = client.get(f"/api/reminders?invoice_id={inv_id}")
    reminders = resp.json()["items"]
    assert len(reminders) == 4
    types = [r["type"] for r in reminders]
    assert "friendly" in types
    assert "escalation" in types


def test_sequential_invoice_numbers(client):
    cid, _ = _setup_client_with_sessions(client, 0)
    # Create sessions one by one and invoice them
    for i in range(3):
        r = client.post(
            "/api/sessions",
            json={
                "client_id": cid,
                "date": f"2025-09-{i + 1:02d}",
                "duration_minutes": 30,
                "hourly_rate": 100.0,
            },
        )
        sid = r.json()["id"]
        r = client.post("/api/invoices", json={"client_id": cid, "session_ids": [sid]})
        num = r.json()["invoice_number"]
        assert num.endswith(f"{i + 1:04d}")
