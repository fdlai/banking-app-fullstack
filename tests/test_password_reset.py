"""Tests for the /auth/forgot-password and /auth/reset-password flow."""

import time

import pytest
from fastapi.testclient import TestClient

from core.security import create_access_token, create_password_reset_token

VALID_REGISTRATION = {
    "first_name": "Nora",
    "last_name": "Reset",
    "email": "nora@example.com",
    "dob": "1995-05-05",
    "password": "original-password",
}


@pytest.fixture
def registered_user(client: TestClient) -> dict:
    response = client.post("/auth/register", json=VALID_REGISTRATION)
    assert response.status_code == 201
    return response.json()


def test_forgot_password_returns_generic_message_for_known_email(
    client: TestClient, registered_user: dict
) -> None:
    response = client.post("/auth/forgot-password", json={"email": "nora@example.com"})

    assert response.status_code == 200
    assert "reset" in response.json()["message"].lower()


def test_forgot_password_returns_same_message_for_unknown_email(
    client: TestClient, registered_user: dict
) -> None:
    known = client.post("/auth/forgot-password", json={"email": "nora@example.com"})
    unknown = client.post("/auth/forgot-password", json={"email": "nobody@example.com"})

    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()


def test_reset_password_with_valid_token_changes_password(
    client: TestClient, registered_user: dict
) -> None:
    user_id = registered_user["user"]["id"]
    reset_token = create_password_reset_token(user_id)

    response = client.post(
        "/auth/reset-password",
        json={"token": reset_token, "new_password": "brand-new-password"},
    )
    assert response.status_code == 200

    old_login = client.post(
        "/auth/login", json={"email": "nora@example.com", "password": "original-password"}
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/auth/login", json={"email": "nora@example.com", "password": "brand-new-password"}
    )
    assert new_login.status_code == 200


def test_reset_password_rejects_garbage_token(client: TestClient) -> None:
    response = client.post(
        "/auth/reset-password",
        json={"token": "not.a.jwt", "new_password": "brand-new-password"},
    )
    assert response.status_code == 400


def test_reset_password_rejects_expired_token(
    client: TestClient, registered_user: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    import core.security as security_module

    monkeypatch.setattr(security_module, "PASSWORD_RESET_EXPIRE_MINUTES", -1)
    user_id = registered_user["user"]["id"]
    expired_token = create_password_reset_token(user_id)

    response = client.post(
        "/auth/reset-password",
        json={"token": expired_token, "new_password": "brand-new-password"},
    )
    assert response.status_code == 400


def test_reset_password_rejects_an_access_token(
    client: TestClient, registered_user: dict
) -> None:
    """A normal login/register access token must not double as a reset token."""
    access_token = registered_user["access_token"]

    response = client.post(
        "/auth/reset-password",
        json={"token": access_token, "new_password": "brand-new-password"},
    )
    assert response.status_code == 400


def test_reset_password_rejects_short_new_password(
    client: TestClient, registered_user: dict
) -> None:
    user_id = registered_user["user"]["id"]
    reset_token = create_password_reset_token(user_id)

    response = client.post(
        "/auth/reset-password",
        json={"token": reset_token, "new_password": "short"},
    )
    assert response.status_code == 422
