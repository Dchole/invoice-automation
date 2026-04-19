def _create_invoice_with_reminders(client):
    r = client.post(
        "/api/clients", json={"name": "Reminder Client", "payment_terms": 30}
    )
    cid = r.json()["id"]
    r = client.post(
        "/api/sessions",
        json={
            "client_id": cid,
            "date": "2025-08-21",
            "duration_minutes": 60,
            "hourly_rate": 150.0,
        },
    )
    sid = r.json()["id"]
    r = client.post("/api/invoices", json={"client_id": cid, "session_ids": [sid]})
    inv_id = r.json()["id"]
    return inv_id


def test_reminders_created_with_invoice(client):
    inv_id = _create_invoice_with_reminders(client)
    resp = client.get(f"/api/reminders?invoice_id={inv_id}")
    assert resp.status_code == 200
    reminders = resp.json()["items"]
    assert len(reminders) == 4
    assert all(r["status"] == "pending" for r in reminders)


def test_send_reminder(client):
    inv_id = _create_invoice_with_reminders(client)
    reminders = client.get(f"/api/reminders?invoice_id={inv_id}").json()["items"]
    rid = reminders[0]["id"]

    resp = client.post(f"/api/reminders/{rid}/send")
    assert resp.status_code == 200
    assert resp.json()["status"] == "sent"
    assert resp.json()["sent_at"] is not None


def test_skip_reminder(client):
    inv_id = _create_invoice_with_reminders(client)
    reminders = client.get(f"/api/reminders?invoice_id={inv_id}").json()["items"]
    rid = reminders[0]["id"]

    resp = client.put(f"/api/reminders/{rid}/skip")
    assert resp.status_code == 200
    assert resp.json()["status"] == "skipped"


def test_payment_skips_pending_reminders(client):
    inv_id = _create_invoice_with_reminders(client)
    client.post(
        "/api/payments",
        json={
            "invoice_id": inv_id,
            "amount": 150.0,
            "payment_date": "2025-09-01",
        },
    )
    reminders = client.get(f"/api/reminders?invoice_id={inv_id}").json()["items"]
    assert all(r["status"] == "skipped" for r in reminders)


def test_filter_reminders_by_status(client):
    inv_id = _create_invoice_with_reminders(client)
    reminders = client.get(f"/api/reminders?invoice_id={inv_id}").json()["items"]
    client.post(f"/api/reminders/{reminders[0]['id']}/send")

    pending = client.get("/api/reminders?status=pending").json()["items"]
    sent = client.get("/api/reminders?status=sent").json()["items"]
    assert len(sent) == 1
    assert len(pending) == 3
