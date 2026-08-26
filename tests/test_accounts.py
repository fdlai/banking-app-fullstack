import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from main import app
from models.account import Account

client = TestClient(app)

UNKNOWN_USER_ID = uuid.uuid4()


def as_user(user_id: uuid.UUID) -> dict:
    return {"X-User-Id": str(user_id)}


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


@pytest.fixture
def account(db, customer):
    account = Account(
        user_id=customer.id,
        account_type="checking",
        balance=Decimal("1000.00"),
        status="active",
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return account


def test_admin_can_list_accounts(admin, account):
    r = client.get(
        "/accounts",
        headers=as_user(admin.id),
    )

    assert r.status_code == 200
    assert len(r.json()) == 1


def test_teller_can_list_accounts(teller, account):
    r = client.get(
        "/accounts",
        headers=as_user(teller.id),
    )

    assert r.status_code == 200
    assert len(r.json()) == 1


def test_customer_cannot_list_all_accounts(customer, account):
    r = client.get(
        "/accounts",
        headers=as_user(customer.id),
    )

    assert r.status_code == 403


def test_admin_can_view_any_account(admin, account):
    r = client.get(
        f"/accounts/{account.id}",
        headers=as_user(admin.id),
    )

    assert r.status_code == 200
    assert r.json()["id"] == account.id


def test_teller_can_view_any_account(teller, account):
    r = client.get(
        f"/accounts/{account.id}",
        headers=as_user(teller.id),
    )

    assert r.status_code == 200
    assert r.json()["id"] == account.id


def test_customer_can_view_own_account(customer, account):
    r = client.get(
        f"/accounts/{account.id}",
        headers=as_user(customer.id),
    )

    assert r.status_code == 200
    assert r.json()["user_id"] == str(customer.id)


def test_customer_cannot_view_other_customers_account(
    other_customer,
    account,
):
    r = client.get(
        f"/accounts/{account.id}",
        headers=as_user(other_customer.id),
    )

    assert r.status_code == 403


def test_missing_account_returns_404(admin):
    r = client.get(
        "/accounts/999999",
        headers=as_user(admin.id),
    )

    assert r.status_code == 404


def test_admin_can_create_account(db, admin, customer):
    body = {
        "user_id": str(customer.id),
        "account_type": "checking",
        "status": "active",
    }

    r = client.post(
        "/accounts",
        json=body,
        headers=as_user(admin.id),
    )

    assert r.status_code == 201

    data = r.json()

    assert data["user_id"] == str(customer.id)
    assert data["account_type"] == "checking"
    assert data["status"] == "active"
    assert Decimal(str(data["balance"])) == Decimal("0.00")

    record = db.get(Account, data["id"])

    assert record is not None
    assert record.user_id == customer.id


def test_teller_can_create_account(teller, customer):
    body = {
        "user_id": str(customer.id),
        "account_type": "savings",
        "status": "active",
    }

    r = client.post(
        "/accounts",
        json=body,
        headers=as_user(teller.id),
    )

    assert r.status_code == 201
    assert r.json()["account_type"] == "savings"


def test_customer_cannot_create_account(customer):
    body = {
        "user_id": str(customer.id),
        "account_type": "checking",
        "status": "active",
    }

    r = client.post(
        "/accounts",
        json=body,
        headers=as_user(customer.id),
    )

    assert r.status_code == 403


def test_create_account_for_missing_user_returns_404(admin):
    body = {
        "user_id": str(UNKNOWN_USER_ID),
        "account_type": "checking",
        "status": "active",
    }

    r = client.post(
        "/accounts",
        json=body,
        headers=as_user(admin.id),
    )

    assert r.status_code == 404


def test_invalid_account_type_is_rejected(admin, customer):
    body = {
        "user_id": str(customer.id),
        "account_type": "banana",
        "status": "active",
    }

    r = client.post(
        "/accounts",
        json=body,
        headers=as_user(admin.id),
    )

    assert r.status_code == 422


def test_invalid_account_status_is_rejected(admin, customer):
    body = {
        "user_id": str(customer.id),
        "account_type": "checking",
        "status": "banana",
    }

    r = client.post(
        "/accounts",
        json=body,
        headers=as_user(admin.id),
    )

    assert r.status_code == 422
