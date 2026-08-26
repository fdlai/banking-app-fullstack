import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient

from main import app
from models.user import User

client = TestClient(app)




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





def test_transfer_success(active_account, second_active_account):
    r = client.post(
        "/transfers",
        json={
            "from_account_id": active_account.id,
            "to_account_id": second_active_account.id,
            "amount": 100
        }
    )

    assert r.status_code == 200

    data = r.json()

    assert data["from_account_id"] == active_account.id
    assert data["to_account_id"] == second_active_account.id
    assert float(data["amount"]) == 100
    assert data["status"] == "completed"


def test_transfer_invalid_amount(active_account, second_active_account):
    r = client.post(
        "/transfers",
        json={
            "from_account_id": active_account.id,
            "to_account_id": second_active_account.id,
            "amount": 0
        }
    )

    assert r.status_code == 400


def test_transfer_negative_amount(active_account, second_active_account):
    r = client.post(
        "/transfers",
        json={
            "from_account_id": active_account.id,
            "to_account_id": second_active_account.id,
            "amount": -50
        }
    )

    assert r.status_code == 400


def test_transfer_same_account(active_account):
    r = client.post(
        "/transfers",
        json={
            "from_account_id": active_account.id,
            "to_account_id": active_account.id,
            "amount": 50
        }
    )

    assert r.status_code == 400


def test_transfer_missing_from_account(active_account):
    r = client.post(
        "/transfers",
        json={
            "from_account_id": 9999,
            "to_account_id": active_account.id,
            "amount": 50
        }
    )

    assert r.status_code == 404


def test_transfer_missing_to_account(active_account):
    r = client.post(
        "/transfers",
        json={
            "from_account_id": active_account.id,
            "to_account_id": 9999,
            "amount": 50
        }
    )

    assert r.status_code == 404

def test_transfer_frozen_from_account(frozen_account, active_account):
    r = client.post(
        "/transfers",
        json={
            "from_account_id": frozen_account.id,
            "to_account_id": active_account.id,
            "amount": 50
        }
    )

    assert r.status_code == 400


def test_transfer_insufficient_funds(active_account, second_active_account):
    r = client.post(
        "/transfers",
        json={
            "from_account_id": active_account.id,
            "to_account_id": second_active_account.id,
            "amount": 999999
        }
    )

    assert r.status_code == 400