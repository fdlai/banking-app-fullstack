from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password
from data.enums import UserRole
from models.account import Account
from models.user import User


def _make_user(db_session: Session, *, email: str, role: UserRole) -> User:
    user = User(
        first_name="Test",
        last_name="User",
        email=email,
        dob=date(1990, 1, 1),
        role=role,
        hashed_password=hash_password("irrelevant-password"),
    )
    db_session.add(user)
    db_session.flush()
    return user


def _auth_headers(user: User) -> dict:
    token = create_access_token(user.id, user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def teller_user(db_session: Session) -> User:
    return _make_user(db_session, email="txn-teller@example.com", role=UserRole.TELLER)


@pytest.fixture
def owner(db_session: Session) -> User:
    return _make_user(db_session, email="txn-owner@example.com", role=UserRole.CUSTOMER)


@pytest.fixture
def other_customer(db_session: Session) -> User:
    return _make_user(db_session, email="txn-other@example.com", role=UserRole.CUSTOMER)


@pytest.fixture
def seeded_accounts(db_session: Session, owner: User):
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
    db_session.add_all(accounts.values())
    db_session.flush()
    return accounts


def test_deposit_success(client: TestClient, teller_user: User, seeded_accounts):
    account_id = seeded_accounts["active"].id
    r = client.post(
        f"/accounts/{account_id}/deposit",
        json={"amount": 100, "description": "test"},
        headers=_auth_headers(teller_user),
    )
    assert r.status_code == 200
    assert r.json()["transaction_type"] == "deposit"


def test_withdraw_success(client: TestClient, teller_user: User, seeded_accounts):
    account_id = seeded_accounts["active"].id
    r = client.post(
        f"/accounts/{account_id}/withdraw",
        json={"amount": 50},
        headers=_auth_headers(teller_user),
    )
    assert r.status_code == 200
    assert r.json()["transaction_type"] == "withdrawal"


def test_deposit_invalid_amount(client: TestClient, teller_user: User, seeded_accounts):
    account_id = seeded_accounts["active"].id
    r = client.post(
        f"/accounts/{account_id}/deposit",
        json={"amount": 0},
        headers=_auth_headers(teller_user),
    )
    assert r.status_code == 400


def test_withdraw_invalid_amount(client: TestClient, teller_user: User, seeded_accounts):
    account_id = seeded_accounts["active"].id
    r = client.post(
        f"/accounts/{account_id}/withdraw",
        json={"amount": -10},
        headers=_auth_headers(teller_user),
    )
    assert r.status_code == 400


def test_frozen_account_rejected(client: TestClient, teller_user: User, seeded_accounts):
    account_id = seeded_accounts["frozen"].id
    r = client.post(
        f"/accounts/{account_id}/deposit",
        json={"amount": 10},
        headers=_auth_headers(teller_user),
    )
    assert r.status_code == 400


def test_withdraw_insufficient_funds(client: TestClient, teller_user: User, seeded_accounts):
    account_id = seeded_accounts["active"].id
    r = client.post(
        f"/accounts/{account_id}/withdraw",
        json={"amount": 999999},
        headers=_auth_headers(teller_user),
    )
    assert r.status_code == 400


def test_deposit_requires_auth(client: TestClient, seeded_accounts):
    account_id = seeded_accounts["active"].id
    r = client.post(f"/accounts/{account_id}/deposit", json={"amount": 10})
    assert r.status_code == 401


def test_customer_cannot_deposit(client: TestClient, owner: User, seeded_accounts):
    account_id = seeded_accounts["active"].id
    r = client.post(
        f"/accounts/{account_id}/deposit",
        json={"amount": 10},
        headers=_auth_headers(owner),
    )
    assert r.status_code == 403


def test_missing_account_404(client: TestClient, teller_user: User, owner: User):
    assert (
        client.post(
            "/accounts/999999999/deposit",
            json={"amount": 10},
            headers=_auth_headers(teller_user),
        ).status_code
        == 404
    )
    assert (
        client.get(
            "/accounts/999999999/transactions",
            headers=_auth_headers(owner),
        ).status_code
        == 404
    )


def test_owner_can_list_own_transactions(client: TestClient, teller_user: User, owner: User, seeded_accounts):
    active_id = seeded_accounts["active"].id
    other_id = seeded_accounts["secondary"].id
    client.post(
        f"/accounts/{active_id}/deposit", json={"amount": 10}, headers=_auth_headers(teller_user)
    )
    client.post(
        f"/accounts/{other_id}/deposit", json={"amount": 10}, headers=_auth_headers(teller_user)
    )

    r = client.get(f"/accounts/{active_id}/transactions", headers=_auth_headers(owner))
    assert r.status_code == 200
    assert len(r.json()) >= 1
    assert all(t["account_id"] == active_id for t in r.json())


def test_other_customer_cannot_list_transactions(
    client: TestClient, other_customer: User, seeded_accounts
):
    account_id = seeded_accounts["active"].id
    r = client.get(f"/accounts/{account_id}/transactions", headers=_auth_headers(other_customer))
    assert r.status_code == 403
