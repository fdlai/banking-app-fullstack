from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

ADMIN, TELLER, CUSTOMER = 1, 2, 3


def as_user(user_id: int) -> dict:
    return {"X-User-Id": str(user_id)}


def test_admin_sees_everyone():
    r = client.get("/users", headers=as_user(ADMIN))
    assert r.status_code == 200
    assert len(r.json()) == 4


def test_teller_sees_only_customers():
    r = client.get("/users", headers=as_user(TELLER))
    assert r.status_code == 200
    assert {u["role"] for u in r.json()} == {"customer"}


def test_customer_cannot_list():
    assert client.get("/users", headers=as_user(CUSTOMER)).status_code == 403


def test_missing_header_is_rejected():
    assert client.get("/users").status_code == 422


def test_unknown_actor_is_unauthorized():
    assert client.get("/users", headers=as_user(99)).status_code == 401


def test_customer_views_self():
    assert client.get("/users/3", headers=as_user(CUSTOMER)).status_code == 200


def test_customer_cannot_view_other_customer():
    assert client.get("/users/4", headers=as_user(CUSTOMER)).status_code == 403


def test_customer_cannot_view_admin():
    assert client.get("/users/1", headers=as_user(CUSTOMER)).status_code == 403


def test_missing_user_is_404():
    assert client.get("/users/99", headers=as_user(ADMIN)).status_code == 404


def test_teller_creates_customer():
    body = {
        "first_name": "New", "last_name": "Customer",
        "email": "new.customer@bank.com", "dob": "1995-01-01",
        "role": "customer",
    }
    assert client.post("/users", json=body, headers=as_user(TELLER)).status_code == 201


def test_teller_cannot_create_admin():
    body = {
        "first_name": "Sneaky", "last_name": "Admin",
        "email": "sneaky@bank.com", "dob": "1995-01-01",
        "role": "admin",
    }
    assert client.post("/users", json=body, headers=as_user(TELLER)).status_code == 403