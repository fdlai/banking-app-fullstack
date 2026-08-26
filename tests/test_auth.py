"""Authentication endpoint tests."""

import jwt
import pytest
from fastapi.testclient import TestClient

VALID_REGISTRATION = {
    "first_name": "Alice",
    "last_name": "Nguyen",
    "email": "alice@example.com",
    "dob": "1998-11-04",
    "password": "correct-horse-battery",
}


@pytest.fixture
def registered_user(client: TestClient) -> dict:
    response = client.post("/auth/register", json=VALID_REGISTRATION)
    assert response.status_code == 201
    return response.json()


def test_register_returns_token_and_user(client: TestClient) -> None:
    response = client.post(
        "/auth/register", json={**VALID_REGISTRATION, "email": "new@example.com"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "new@example.com"
    assert body["user"]["role"] == "customer"
    assert body["user"]["full_name"] == "Alice Nguyen"


def test_register_never_returns_password_hash(client: TestClient, registered_user: dict) -> None:
    assert "hashed_password" not in registered_user["user"]
    assert "password" not in registered_user["user"]


def test_register_rejects_duplicate_email(client: TestClient, registered_user: dict) -> None:
    response = client.post("/auth/register", json=VALID_REGISTRATION)
    assert response.status_code == 409


def test_register_rejects_short_password(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={**VALID_REGISTRATION, "email": "short@example.com", "password": "abc"},
    )
    assert response.status_code == 422


def test_register_rejects_future_dob(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={**VALID_REGISTRATION, "email": "future@example.com", "dob": "2099-01-01"},
    )
    assert response.status_code == 422


def test_register_rejects_blank_name(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={**VALID_REGISTRATION, "email": "blank@example.com", "first_name": "   "},
    )
    assert response.status_code == 422


def test_register_ignores_client_supplied_role(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={**VALID_REGISTRATION, "email": "sneaky@example.com", "role": "admin"},
    )
    assert response.status_code == 201
    assert response.json()["user"]["role"] == "customer"


def test_login_succeeds_with_correct_password(client: TestClient, registered_user: dict) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "correct-horse-battery"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_fails_with_wrong_password(client: TestClient, registered_user: dict) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_login_does_not_reveal_whether_email_exists(client: TestClient, registered_user: dict) -> None:
    missing = client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "correct-horse-battery"},
    )
    wrong = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "wrong-password"},
    )
    assert missing.status_code == wrong.status_code == 401
    assert missing.json()["detail"] == wrong.json()["detail"]


def test_me_returns_the_authenticated_user(client: TestClient, registered_user: dict) -> None:
    token = registered_user["access_token"]
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.com"


def test_me_rejects_missing_token(client: TestClient) -> None:
    assert client.get("/auth/me").status_code == 401


def test_me_rejects_garbage_token(client: TestClient) -> None:
    response = client.get("/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert response.status_code == 401


def test_me_rejects_token_signed_with_another_key(client: TestClient) -> None:
    forged = jwt.encode({"sub": "1", "role": "admin"}, "attacker-key", algorithm="HS256")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401