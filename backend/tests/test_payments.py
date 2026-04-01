def _create_invoice(client):
    r = client.post("/api/clients", json={"name": "Pay Client", "payment_terms": 30})
    cid = r.json()["id"]
    r = client.post("/api/sessions", json={
        "client_id": cid, "date": "2025-08-21",
        "duration_minutes": 60, "hourly_rate": 200.0,
    })
    sid = r.json()["id"]
    r = client.post("/api/invoices", json={"client_id": cid, "session_ids": [sid]})
    return r.json()["id"], sid


def test_record_full_payment(client):
    inv_id, sid = _create_invoice(client)
    resp = client.post("/api/payments", json={
        "invoice_id": inv_id,
        "amount": 200.0,
        "payment_date": "2025-09-01",
        "payment_method": "e-transfer",
    })
    assert resp.status_code == 201

    # Invoice should be paid
    inv = client.get(f"/api/invoices/{inv_id}").json()
    assert inv["status"] == "paid"
    assert inv["paid_at"] is not None

    # Session should be paid
    s = client.get(f"/api/sessions/{sid}").json()
    assert s["status"] == "paid"

    # Reminders should be skipped
    reminders = client.get(f"/api/reminders?invoice_id={inv_id}").json()
    for r in reminders:
        assert r["status"] == "skipped"


def test_partial_payment(client):
    inv_id, sid = _create_invoice(client)
    client.post("/api/payments", json={
        "invoice_id": inv_id, "amount": 100.0,
        "payment_date": "2025-09-01",
    })

    inv = client.get(f"/api/invoices/{inv_id}").json()
    assert inv["status"] != "paid"
    assert inv["amount_paid"] == 100.0

    # Second payment completes it
    client.post("/api/payments", json={
        "invoice_id": inv_id, "amount": 100.0,
        "payment_date": "2025-09-05",
    })
    inv = client.get(f"/api/invoices/{inv_id}").json()
    assert inv["status"] == "paid"


def test_bulk_payments(client):
    inv_id1, _ = _create_invoice(client)
    # Create a second client+invoice
    r = client.post("/api/clients", json={"name": "Pay Client 2"})
    cid2 = r.json()["id"]
    r = client.post("/api/sessions", json={
        "client_id": cid2, "date": "2025-08-22",
        "duration_minutes": 30, "hourly_rate": 100.0,
    })
    sid2 = r.json()["id"]
    r = client.post("/api/invoices", json={"client_id": cid2, "session_ids": [sid2]})
    inv_id2 = r.json()["id"]

    resp = client.post("/api/payments/bulk", json=[
        {"invoice_id": inv_id1, "amount": 200.0, "payment_date": "2025-09-01"},
        {"invoice_id": inv_id2, "amount": 50.0, "payment_date": "2025-09-01"},
    ])
    assert resp.status_code == 201
    assert len(resp.json()) == 2


def test_list_payments(client):
    inv_id, _ = _create_invoice(client)
    client.post("/api/payments", json={
        "invoice_id": inv_id, "amount": 50.0, "payment_date": "2025-09-01",
    })
    client.post("/api/payments", json={
        "invoice_id": inv_id, "amount": 50.0, "payment_date": "2025-09-05",
    })
    resp = client.get(f"/api/payments?invoice_id={inv_id}")
    assert len(resp.json()) == 2
