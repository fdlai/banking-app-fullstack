from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from data.mock_data import accounts, transactions

router = APIRouter(prefix="/accounts", tags=["transactions"])


class TransactionCreate(BaseModel):
    amount: float
    description: str | None = None


def get_account(account_id: int):
    for account in accounts:
        if account["id"] == account_id:
            return account

    raise HTTPException(
        status_code=404,
        detail="Account not found"
    )


def record_transaction(account_id: int, transaction_type: str, amount: float, description: str | None):
    new_id = max((t["id"] for t in transactions), default=0) + 1

    transaction = {
        "id": new_id,
        "account_id": account_id,
        "transaction_type": transaction_type,
        "amount": amount,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "description": description,
    }

    transactions.append(transaction)

    return transaction


@router.post("/{account_id}/deposit")
def deposit(account_id: int, request: TransactionCreate):
    if request.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Deposit amount must be greater than zero"
        )

    account = get_account(account_id)

    # frozen/closed accounts can't transact
    if account["status"] != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Account is {account['status']} and cannot accept deposits"
        )

    account["balance"] += request.amount

    return record_transaction(account_id, "deposit", request.amount, request.description)


@router.post("/{account_id}/withdraw")
def withdraw(account_id: int, request: TransactionCreate):
    if request.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Withdrawal amount must be greater than zero"
        )

    account = get_account(account_id)

    # frozen/closed accounts can't transact
    if account["status"] != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Account is {account['status']} and cannot process withdrawals"
        )

    if request.amount > account["balance"]:
        raise HTTPException(
            status_code=400,
            detail="Insufficient funds"
        )

    account["balance"] -= request.amount

    return record_transaction(account_id, "withdrawal", request.amount, request.description)


@router.get("/{account_id}/transactions")
def get_account_transactions(account_id: int):
    get_account(account_id)

    return [t for t in transactions if t["account_id"] == account_id]
