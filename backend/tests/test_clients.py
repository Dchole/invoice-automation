def test_create_client(client):
    resp = client.post("/api/clients", json={
        "name": "Acme Corp",
        "email": "billing@acme.com",
        "currency": "USD",
        "default_rate": 150.00,
        "payment_terms": 30,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Acme Corp"
    assert data["currency"] == "USD"
    assert data["default_rate"] == 150.0
    assert data["status"] == "active"
    assert data["id"] > 0


def test_list_clients(client):
    client.post("/api/clients", json={"name": "Client A"})
    client.post("/api/clients", json={"name": "Client B"})
    resp = client.get("/api/clients")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_clients_filter_by_status(client):
    client.post("/api/clients", json={"name": "Active Client"})
    r = client.post("/api/clients", json={"name": "Inactive Client"})
    cid = r.json()["id"]
    client.put(f"/api/clients/{cid}", json={"status": "inactive"})

    resp = client.get("/api/clients?status=active")
    assert len(resp.json()) == 1
    assert resp.json()[0]["name"] == "Active Client"


def test_get_client(client):
    r = client.post("/api/clients", json={"name": "Solo Client"})
    cid = r.json()["id"]
    resp = client.get(f"/api/clients/{cid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Solo Client"


def test_get_client_not_found(client):
    resp = client.get("/api/clients/9999")
    assert resp.status_code == 404


def test_update_client(client):
    r = client.post("/api/clients", json={"name": "Old Name"})
    cid = r.json()["id"]
    resp = client.put(f"/api/clients/{cid}", json={"name": "New Name", "currency": "USD"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"
    assert resp.json()["currency"] == "USD"


def test_delete_client(client):
    r = client.post("/api/clients", json={"name": "To Delete"})
    cid = r.json()["id"]
    resp = client.delete(f"/api/clients/{cid}")
    assert resp.status_code == 204
    resp = client.get(f"/api/clients/{cid}")
    assert resp.status_code == 404
