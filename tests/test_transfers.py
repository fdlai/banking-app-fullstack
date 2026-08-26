from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_transfer_success():
    r = client.post(
        "/transfers",
        json={
            "from_account_id": 101,
            "to_account_id": 103,
            "amount": 100
        }
    )

    assert r.status_code == 200

    data = r.json()

    assert data["from_account_id"] == 101
    assert data["to_account_id"] == 103
    assert float(data["amount"]) == 100
    assert data["status"] == "completed"


def test_transfer_invalid_amount():
    r = client.post(
        "/transfers",
        json={
            "from_account_id": 101,
            "to_account_id": 103,
            "amount": 0
        }
    )

    assert r.status_code == 400


def test_transfer_negative_amount():
    r = client.post(
        "/transfers",
        json={
            "from_account_id": 101,
            "to_account_id": 103,
            "amount": -50
        }
    )

    assert r.status_code == 400


def test_transfer_same_account():
    r = client.post(
        "/transfers",
        json={
            "from_account_id": 101,
            "to_account_id": 101,
            "amount": 50
        }
    )

    assert r.status_code == 400


def test_transfer_missing_from_account():
    r = client.post(
        "/transfers",
        json={
            "from_account_id": 9999,
            "to_account_id": 103,
            "amount": 50
        }
    )

    assert r.status_code == 404


def test_transfer_missing_to_account():
    r = client.post(
        "/transfers",
        json={
            "from_account_id": 101,
            "to_account_id": 9999,
            "amount": 50
        }
    )

    assert r.status_code == 404


def test_transfer_insufficient_funds():
    r = client.post(
        "/transfers",
        json={
            "from_account_id": 105,
            "to_account_id": 103,
            "amount": 999999
        }
    )

    assert r.status_code == 400


def test_transfer_frozen_from_account():
    r = client.post(
        "/transfers",
        json={
            "from_account_id": 112,
            "to_account_id": 103,
            "amount": 50
        }
    )

    assert r.status_code == 400