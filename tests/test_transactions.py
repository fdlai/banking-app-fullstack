from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from main import app
from models.account import Account
from models.user import User, UserRole

client = TestClient(app)


@pytest.fixture
def owner(db):
    user = User(
        role=UserRole.CUSTOMER,
        first_name="Owen",
        last_name="Owner",
        email="owen.owner@example.com",
        dob=date(1990, 1, 1),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def seeded_accounts(db, owner):
    """Two active accounts (to prove listing is filtered per-account) plus one frozen."""
    accounts = {
        "active": Account(
            user_id=owner.id, account_type="checking", balance=Decimal("500.00"), status="active"
        ),
        "secondary": Account(
            user_id=owner.id, account_type="savings", balance=Decimal("500.00"), status="active"
        ),
        "frozen": Account(
            user_id=owner.id, account_type="checking", balance=Decimal("100.00"), status="frozen"
        ),
    }
    db.add_all(accounts.values())
    db.commit()
    for account in accounts.values():
        db.refresh(account)
    return accounts


def test_deposit_success(seeded_accounts):
    account_id = seeded_accounts["active"].id
    r = client.post(f"/accounts/{account_id}/deposit", json={"amount": 100, "description": "test"})
    assert r.status_code == 200
    assert r.json()["transaction_type"] == "deposit"


def test_withdraw_success(seeded_accounts):
    account_id = seeded_accounts["active"].id
    r = client.post(f"/accounts/{account_id}/withdraw", json={"amount": 50})
    assert r.status_code == 200
    assert r.json()["transaction_type"] == "withdrawal"


def test_deposit_invalid_amount(seeded_accounts):
    account_id = seeded_accounts["active"].id
    assert client.post(f"/accounts/{account_id}/deposit", json={"amount": 0}).status_code == 400


def test_withdraw_invalid_amount(seeded_accounts):
    account_id = seeded_accounts["active"].id
    assert client.post(f"/accounts/{account_id}/withdraw", json={"amount": -10}).status_code == 400


def test_frozen_account_rejected(seeded_accounts):
    account_id = seeded_accounts["frozen"].id
    assert client.post(f"/accounts/{account_id}/deposit", json={"amount": 10}).status_code == 400


def test_withdraw_insufficient_funds(seeded_accounts):
    account_id = seeded_accounts["active"].id
    assert client.post(f"/accounts/{account_id}/withdraw", json={"amount": 999999}).status_code == 400


def test_missing_account_404():
    assert client.post("/accounts/999999999/deposit", json={"amount": 10}).status_code == 404
    assert client.get("/accounts/999999999/transactions").status_code == 404


def test_list_transactions_filtered_to_account(seeded_accounts):
    active_id = seeded_accounts["active"].id
    other_id = seeded_accounts["secondary"].id
    client.post(f"/accounts/{active_id}/deposit", json={"amount": 10})
    client.post(f"/accounts/{other_id}/deposit", json={"amount": 10})

    r = client.get(f"/accounts/{active_id}/transactions")
    assert r.status_code == 200
    assert len(r.json()) >= 1
    assert all(t["account_id"] == active_id for t in r.json())
