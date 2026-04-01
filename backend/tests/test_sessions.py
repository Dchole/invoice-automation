def _create_client(client, name="Test Client"):
    r = client.post("/api/clients", json={"name": name, "default_rate": 150.0})
    return r.json()["id"]


def test_create_session_with_duration(client):
    cid = _create_client(client)
    resp = client.post("/api/sessions", json={
        "client_id": cid,
        "date": "2025-08-21",
        "duration_minutes": 60,
        "hourly_rate": 150.0,
        "description": "Strategy consulting",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == 150.0
    assert data["status"] == "unbilled"
    assert data["duration_minutes"] == 60


def test_create_session_computes_duration_from_times(client):
    cid = _create_client(client)
    resp = client.post("/api/sessions", json={
        "client_id": cid,
        "date": "2025-08-21",
        "start_time": "09:00",
        "end_time": "10:30",
        "hourly_rate": 200.0,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["duration_minutes"] == 90
    assert data["amount"] == 300.0


def test_create_session_requires_duration_or_times(client):
    cid = _create_client(client)
    resp = client.post("/api/sessions", json={
        "client_id": cid,
        "date": "2025-08-21",
        "hourly_rate": 150.0,
    })
    assert resp.status_code == 422


def test_list_unbilled_sessions(client):
    cid = _create_client(client)
    client.post("/api/sessions", json={
        "client_id": cid, "date": "2025-08-21",
        "duration_minutes": 60, "hourly_rate": 150.0,
    })
    client.post("/api/sessions", json={
        "client_id": cid, "date": "2025-08-22",
        "duration_minutes": 45, "hourly_rate": 150.0,
    })
    resp = client.get("/api/sessions/unbilled")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_bulk_create_sessions(client):
    cid = _create_client(client)
    resp = client.post("/api/sessions/bulk", json=[
        {"client_id": cid, "date": "2025-08-21", "duration_minutes": 60, "hourly_rate": 150.0},
        {"client_id": cid, "date": "2025-08-22", "duration_minutes": 30, "hourly_rate": 150.0},
    ])
    assert resp.status_code == 201
    assert len(resp.json()) == 2


def test_update_session_recalculates_amount(client):
    cid = _create_client(client)
    r = client.post("/api/sessions", json={
        "client_id": cid, "date": "2025-08-21",
        "duration_minutes": 60, "hourly_rate": 150.0,
    })
    sid = r.json()["id"]
    resp = client.put(f"/api/sessions/{sid}", json={"hourly_rate": 200.0})
    assert resp.status_code == 200
    assert resp.json()["amount"] == 200.0


def test_cannot_delete_invoiced_session(client):
    cid = _create_client(client)
    r = client.post("/api/sessions", json={
        "client_id": cid, "date": "2025-08-21",
        "duration_minutes": 60, "hourly_rate": 150.0,
    })
    sid = r.json()["id"]
    # Generate invoice for this session
    client.post("/api/invoices", json={
        "client_id": cid, "session_ids": [sid],
    })
    resp = client.delete(f"/api/sessions/{sid}")
    assert resp.status_code == 400
