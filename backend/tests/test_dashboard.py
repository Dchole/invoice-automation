def _seed_data(client):
    """Create a realistic scenario with mixed payment states."""
    # Two clients
    r = client.post("/api/clients", json={"name": "Good Payer", "payment_terms": 30, "currency": "CAD"})
    c1 = r.json()["id"]
    r = client.post("/api/clients", json={"name": "Slow Payer", "payment_terms": 15, "currency": "USD"})
    c2 = r.json()["id"]

    # Sessions for client 1 (will be fully paid)
    r = client.post("/api/sessions", json={
        "client_id": c1, "date": "2025-08-01", "duration_minutes": 60, "hourly_rate": 150.0,
    })
    s1 = r.json()["id"]

    # Sessions for client 2 (will be invoiced but unpaid)
    r = client.post("/api/sessions", json={
        "client_id": c2, "date": "2025-08-15", "duration_minutes": 90, "hourly_rate": 225.0,
    })
    s2 = r.json()["id"]

    # Unbilled session for client 1
    client.post("/api/sessions", json={
        "client_id": c1, "date": "2025-09-01", "duration_minutes": 45, "hourly_rate": 150.0,
    })

    # Invoice and pay client 1
    r = client.post("/api/invoices", json={"client_id": c1, "session_ids": [s1]})
    inv1 = r.json()["id"]
    client.post(f"/api/invoices/{inv1}/send")
    client.post("/api/payments", json={
        "invoice_id": inv1, "amount": 150.0, "payment_date": "2025-08-15",
    })

    # Invoice client 2 but don't pay
    r = client.post("/api/invoices", json={"client_id": c2, "session_ids": [s2]})
    inv2 = r.json()["id"]
    client.post(f"/api/invoices/{inv2}/send")

    return c1, c2, inv1, inv2


def test_dashboard_summary(client):
    _seed_data(client)
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_clients"] == 2
    assert data["total_invoices"] == 2
    assert data["paid_invoices"] == 1
    # Unbilled amount = 45 min * $150/hr = $112.50
    assert data["unbilled_amount"] == 112.5


def test_dashboard_aging(client):
    _seed_data(client)
    resp = client.get("/api/dashboard/aging")
    assert resp.status_code == 200
    data = resp.json()
    # All buckets should be floats
    assert isinstance(data["current"], float)
    assert isinstance(data["days_30"], float)
    assert isinstance(data["days_60"], float)
    assert isinstance(data["days_90_plus"], float)


def test_dashboard_client_scores(client):
    _seed_data(client)
    resp = client.get("/api/dashboard/client-scores")
    assert resp.status_code == 200
    scores = resp.json()
    assert len(scores) == 2
    names = {s["client_name"] for s in scores}
    assert "Good Payer" in names
    assert "Slow Payer" in names

    good = next(s for s in scores if s["client_name"] == "Good Payer")
    assert good["outstanding_balance"] == 0
    assert good["total_paid"] == 150.0


def test_dashboard_cashflow(client):
    _seed_data(client)
    resp = client.get("/api/dashboard/cashflow?days=90")
    assert resp.status_code == 200
    points = resp.json()
    assert len(points) > 0
    assert "date" in points[0]
    assert "expected_amount" in points[0]
    assert "cumulative" in points[0]
