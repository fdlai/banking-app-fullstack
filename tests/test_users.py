import copy

import pytest
from fastapi.testclient import TestClient

from data import mock_data
from main import app

client = TestClient(app)

# ids from data/mock_data.py — the shared source of truth
ADMIN, CUSTOMER, OTHER_CUSTOMER = 9, 1, 2

CUSTOMER_COUNT = 8
TOTAL_USERS = len(mock_data.users)


@pytest.fixture(autouse=True)
def restore_users():
    """mock_data.users is shared mutable state — put it back after each test."""
    original = copy.deepcopy(mock_data.users)
    yield
    mock_data.users[:] = original


@pytest.fixture
def teller_id():
    """mock_data has no teller, so create one for the role-specific tests."""
    body = {
        "first_name": "Test", "last_name": "Teller",
        "email": "test.teller@bank.com", "dob": "1990-01-01",
        "role": "teller",
    }
    r = client.post("/users", json=body, headers=as_user(ADMIN))
    assert r.status_code == 201
    return r.json()["id"]


def as_user(user_id: int) -> dict:
    return {"X-User-Id": str(user_id)}


def test_admin_sees_everyone():
    r = client.get("/users", headers=as_user(ADMIN))
    assert r.status_code == 200
    assert len(r.json()) == TOTAL_USERS


def test_teller_sees_only_customers(teller_id):
    r = client.get("/users", headers=as_user(teller_id))
    assert r.status_code == 200
    assert {u["role"] for u in r.json()} == {"customer"}
    assert len(r.json()) == CUSTOMER_COUNT


def test_customer_cannot_list():
    assert client.get("/users", headers=as_user(CUSTOMER)).status_code == 403


def test_missing_header_is_rejected():
    assert client.get("/users").status_code == 422


def test_unknown_actor_is_unauthorized():
    assert client.get("/users", headers=as_user(999)).status_code == 401


def test_customer_views_self():
    r = client.get(f"/users/{CUSTOMER}", headers=as_user(CUSTOMER))
    assert r.status_code == 200
    assert r.json()["dob"] == "1988-03-12"


def test_customer_cannot_view_other_customer():
    r = client.get(f"/users/{OTHER_CUSTOMER}", headers=as_user(CUSTOMER))
    assert r.status_code == 403


def test_customer_cannot_view_admin():
    assert client.get(f"/users/{ADMIN}", headers=as_user(CUSTOMER)).status_code == 403


def test_missing_user_is_404():
    assert client.get("/users/999", headers=as_user(ADMIN)).status_code == 404


def test_teller_creates_customer(teller_id):
    body = {
        "first_name": "New", "last_name": "Customer",
        "email": "new.customer@bank.com", "dob": "1995-01-01",
        "role": "customer",
    }
    r = client.post("/users", json=body, headers=as_user(teller_id))
    assert r.status_code == 201
    assert r.json()["dob"] == "1995-01-01"


def test_teller_cannot_create_admin(teller_id):
    body = {
        "first_name": "Sneaky", "last_name": "Admin",
        "email": "sneaky@bank.com", "dob": "1995-01-01",
        "role": "admin",
    }
    assert client.post("/users", json=body, headers=as_user(teller_id)).status_code == 403


def test_duplicate_email_is_rejected():
    body = {
        "first_name": "Copy", "last_name": "Cat",
        "email": "alice.johnson@yahoo.com", "dob": "1995-01-01",
        "role": "customer",
    }
    assert client.post("/users", json=body, headers=as_user(ADMIN)).status_code == 409


def test_created_user_lands_in_mock_data():
    body = {
        "first_name": "Shared", "last_name": "Record",
        "email": "shared.record@bank.com", "dob": "1999-02-03",
        "role": "customer",
    }
    new_id = client.post("/users", json=body, headers=as_user(ADMIN)).json()["id"]
    record = next(u for u in mock_data.users if u["id"] == new_id)
    assert record["email"] == "shared.record@bank.com"
    assert record["dob"] == "1999-02-03"


def test_update_writes_through_to_mock_data():
    r = client.patch(
        f"/users/{CUSTOMER}",
        json={"last_name": "Renamed"},
        headers=as_user(ADMIN),
    )
    assert r.status_code == 200
    record = next(u for u in mock_data.users if u["id"] == CUSTOMER)
    assert record["last_name"] == "Renamed"
    assert record["dob"] == "1988-03-12"


def test_delete_removes_from_mock_data():
    assert client.delete(f"/users/{CUSTOMER}", headers=as_user(ADMIN)).status_code == 204
    assert all(u["id"] != CUSTOMER for u in mock_data.users)


def test_customer_cannot_delete():
    r = client.delete(f"/users/{OTHER_CUSTOMER}", headers=as_user(CUSTOMER))
    assert r.status_code == 403
