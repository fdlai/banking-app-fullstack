"""Tests for the admin-only account freeze/unfreeze endpoints."""

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


def _make_account(db_session: Session, *, user_id, status: str = "active") -> Account:
    account = Account(
        user_id=user_id,
        account_type="checking",
        balance=Decimal("100.00"),
        status=status,
    )
    db_session.add(account)
    db_session.flush()
    return account


def _auth_headers(user: User) -> dict:
    token = create_access_token(user.id, user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db_session: Session) -> User:
    return _make_user(db_session, email="freeze-admin@example.com", role=UserRole.ADMIN)


@pytest.fixture
def teller_user(db_session: Session) -> User:
    return _make_user(db_session, email="freeze-teller@example.com", role=UserRole.TELLER)


@pytest.fixture
def customer_user(db_session: Session) -> User:
    return _make_user(db_session, email="freeze-customer@example.com", role=UserRole.CUSTOMER)


def test_admin_can_freeze_active_account(
    client: TestClient, db_session: Session, admin_user: User, customer_user: User
) -> None:
    account = _make_account(db_session, user_id=customer_user.id)

    response = client.patch(f"/accounts/{account.id}/freeze", headers=_auth_headers(admin_user))

    assert response.status_code == 200
    assert response.json()["status"] == "frozen"


def test_admin_can_unfreeze_frozen_account(
    client: TestClient, db_session: Session, admin_user: User, customer_user: User
) -> None:
    account = _make_account(db_session, user_id=customer_user.id, status="frozen")

    response = client.patch(f"/accounts/{account.id}/unfreeze", headers=_auth_headers(admin_user))

    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_customer_cannot_freeze_account(
    client: TestClient, db_session: Session, customer_user: User
) -> None:
    account = _make_account(db_session, user_id=customer_user.id)

    response = client.patch(f"/accounts/{account.id}/freeze", headers=_auth_headers(customer_user))

    assert response.status_code == 403


def test_teller_cannot_freeze_account(
    client: TestClient, db_session: Session, teller_user: User, customer_user: User
) -> None:
    account = _make_account(db_session, user_id=customer_user.id)

    response = client.patch(f"/accounts/{account.id}/freeze", headers=_auth_headers(teller_user))

    assert response.status_code == 403


def test_cannot_freeze_closed_account(
    client: TestClient, db_session: Session, admin_user: User, customer_user: User
) -> None:
    account = _make_account(db_session, user_id=customer_user.id, status="closed")

    response = client.patch(f"/accounts/{account.id}/freeze", headers=_auth_headers(admin_user))

    assert response.status_code == 400


def test_cannot_unfreeze_closed_account(
    client: TestClient, db_session: Session, admin_user: User, customer_user: User
) -> None:
    account = _make_account(db_session, user_id=customer_user.id, status="closed")

    response = client.patch(f"/accounts/{account.id}/unfreeze", headers=_auth_headers(admin_user))

    assert response.status_code == 400


def test_cannot_unfreeze_account_that_is_not_frozen(
    client: TestClient, db_session: Session, admin_user: User, customer_user: User
) -> None:
    account = _make_account(db_session, user_id=customer_user.id, status="active")

    response = client.patch(f"/accounts/{account.id}/unfreeze", headers=_auth_headers(admin_user))

    assert response.status_code == 400


def test_freeze_missing_account_returns_404(client: TestClient, admin_user: User) -> None:
    response = client.patch("/accounts/999999/freeze", headers=_auth_headers(admin_user))

    assert response.status_code == 404


def test_unfreeze_missing_account_returns_404(client: TestClient, admin_user: User) -> None:
    response = client.patch("/accounts/999999/unfreeze", headers=_auth_headers(admin_user))

    assert response.status_code == 404
