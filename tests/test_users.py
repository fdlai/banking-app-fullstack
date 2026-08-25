import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient

from main import app
from models.user import User

client = TestClient(app)

# Seeded by the `seeded_users` fixture: 1 admin, 1 teller, 2 customers.
TOTAL_USERS = 4
CUSTOMER_COUNT = 2

UNKNOWN = uuid.uuid4()


@pytest.fixture
def admin(seeded_users):
    return seeded_users["admin"]


@pytest.fixture
def teller(seeded_users):
    return seeded_users["teller"]


@pytest.fixture
def customer(seeded_users):
    return seeded_users["customer"]


@pytest.fixture
def other_customer(seeded_users):
    return seeded_users["other_customer"]


def as_user(user_id: uuid.UUID) -> dict:
    return {"X-User-Id": str(user_id)}


def test_admin_sees_everyone(admin):
    r = client.get("/users", headers=as_user(admin.id))
    assert r.status_code == 200
    assert len(r.json()) == TOTAL_USERS


def test_teller_sees_only_customers(teller):
    r = client.get("/users", headers=as_user(teller.id))
    assert r.status_code == 200
    assert {u["role"] for u in r.json()} == {"customer"}
    assert len(r.json()) == CUSTOMER_COUNT


def test_customer_cannot_list(customer):
    assert client.get("/users", headers=as_user(customer.id)).status_code == 403


def test_missing_header_is_rejected():
    assert client.get("/users").status_code == 422


def test_unknown_actor_is_unauthorized():
    assert client.get("/users", headers=as_user(UNKNOWN)).status_code == 401


def test_customer_views_self(customer):
    r = client.get(f"/users/{customer.id}", headers=as_user(customer.id))
    assert r.status_code == 200
    assert r.json()["dob"] == customer.dob.isoformat()


def test_customer_cannot_view_other_customer(customer, other_customer):
    r = client.get(f"/users/{other_customer.id}", headers=as_user(customer.id))
    assert r.status_code == 403


def test_customer_cannot_view_admin(customer, admin):
    assert client.get(f"/users/{admin.id}", headers=as_user(customer.id)).status_code == 403


def test_missing_user_is_404(admin):
    assert client.get(f"/users/{UNKNOWN}", headers=as_user(admin.id)).status_code == 404


def test_teller_creates_customer(teller):
    body = {
        "first_name": "New", "last_name": "Customer",
        "email": "new.customer@bank.com", "dob": "1995-01-01",
        "role": "customer",
    }
    r = client.post("/users", json=body, headers=as_user(teller.id))
    assert r.status_code == 201
    assert r.json()["dob"] == "1995-01-01"


def test_teller_cannot_create_admin(teller):
    body = {
        "first_name": "Sneaky", "last_name": "Admin",
        "email": "sneaky@bank.com", "dob": "1995-01-01",
        "role": "admin",
    }
    assert client.post("/users", json=body, headers=as_user(teller.id)).status_code == 403


def test_duplicate_email_is_rejected(admin, customer):
    body = {
        "first_name": "Copy", "last_name": "Cat",
        "email": customer.email, "dob": "1995-01-01",
        "role": "customer",
    }
    assert client.post("/users", json=body, headers=as_user(admin.id)).status_code == 409


def test_created_user_is_persisted(db, admin):
    body = {
        "first_name": "Shared", "last_name": "Record",
        "email": "shared.record@bank.com", "dob": "1999-02-03",
        "role": "customer",
    }
    new_id = client.post("/users", json=body, headers=as_user(admin.id)).json()["id"]
    record = db.get(User, new_id)
    assert record.email == "shared.record@bank.com"
    assert record.dob == date(1999, 2, 3)


def test_update_is_persisted(db, admin, customer):
    r = client.patch(
        f"/users/{customer.id}",
        json={"last_name": "Renamed"},
        headers=as_user(admin.id),
    )
    assert r.status_code == 200
    record = db.get(User, customer.id)
    assert record.last_name == "Renamed"
    assert record.dob == date(1988, 3, 12)


def test_delete_is_persisted(db, admin, customer):
    assert client.delete(f"/users/{customer.id}", headers=as_user(admin.id)).status_code == 204
    assert db.get(User, customer.id) is None


def test_customer_cannot_delete(customer, other_customer):
    r = client.delete(f"/users/{other_customer.id}", headers=as_user(customer.id))
    assert r.status_code == 403
