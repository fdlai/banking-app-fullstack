"""Tests for the admin-only user role-update endpoint."""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password
from data.enums import UserRole
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
def admin_user(db_session: Session) -> User:
    return _make_user(db_session, email="role-admin@example.com", role=UserRole.ADMIN)


@pytest.fixture
def teller_user(db_session: Session) -> User:
    return _make_user(db_session, email="role-teller@example.com", role=UserRole.TELLER)


@pytest.fixture
def customer_user(db_session: Session) -> User:
    return _make_user(db_session, email="role-customer@example.com", role=UserRole.CUSTOMER)


def test_admin_can_promote_customer_to_teller(
    client: TestClient, admin_user: User, customer_user: User
) -> None:
    response = client.patch(
        f"/users/{customer_user.id}/role",
        json={"role": "teller"},
        headers=_auth_headers(admin_user),
    )

    assert response.status_code == 200
    assert response.json()["role"] == "teller"


def test_admin_can_demote_teller_to_customer(
    client: TestClient, admin_user: User, teller_user: User
) -> None:
    response = client.patch(
        f"/users/{teller_user.id}/role",
        json={"role": "customer"},
        headers=_auth_headers(admin_user),
    )

    assert response.status_code == 200
    assert response.json()["role"] == "customer"


def test_teller_cannot_update_role(
    client: TestClient, teller_user: User, customer_user: User
) -> None:
    response = client.patch(
        f"/users/{customer_user.id}/role",
        json={"role": "admin"},
        headers=_auth_headers(teller_user),
    )

    assert response.status_code == 403


def test_customer_cannot_update_own_role(
    client: TestClient, customer_user: User
) -> None:
    response = client.patch(
        f"/users/{customer_user.id}/role",
        json={"role": "admin"},
        headers=_auth_headers(customer_user),
    )

    assert response.status_code == 403


def test_update_role_for_missing_user_returns_404(
    client: TestClient, admin_user: User
) -> None:
    response = client.patch(
        "/users/00000000-0000-0000-0000-000000000000/role",
        json={"role": "admin"},
        headers=_auth_headers(admin_user),
    )

    assert response.status_code == 404


def test_update_role_rejects_invalid_role(
    client: TestClient, admin_user: User, customer_user: User
) -> None:
    response = client.patch(
        f"/users/{customer_user.id}/role",
        json={"role": "superuser"},
        headers=_auth_headers(admin_user),
    )

    assert response.status_code == 422
