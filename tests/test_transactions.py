from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_deposit_success():
    r = client.post("/accounts/101/deposit", json={"amount": 100, "description": "test"})
    assert r.status_code == 200
    assert r.json()["transaction_type"] == "deposit"


def test_withdraw_success():
    r = client.post("/accounts/103/withdraw", json={"amount": 50})
    assert r.status_code == 200
    assert r.json()["transaction_type"] == "withdrawal"


def test_deposit_invalid_amount():
    assert client.post("/accounts/101/deposit", json={"amount": 0}).status_code == 400


def test_withdraw_invalid_amount():
    assert client.post("/accounts/101/withdraw", json={"amount": -10}).status_code == 400


def test_frozen_account_rejected():
    assert client.post("/accounts/112/deposit", json={"amount": 10}).status_code == 400


def test_withdraw_insufficient_funds():
    assert client.post("/accounts/105/withdraw", json={"amount": 999999}).status_code == 400


def test_missing_account_404():
    assert client.post("/accounts/9999/deposit", json={"amount": 10}).status_code == 404
    assert client.get("/accounts/9999/transactions").status_code == 404


def test_list_transactions_filtered_to_account():
    r = client.get("/accounts/101/transactions")
    assert r.status_code == 200
    assert all(t["account_id"] == 101 for t in r.json())
