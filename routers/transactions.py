from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from database import get_db
from models.account import Account
from models.transactions import Transaction

router = APIRouter(prefix="/accounts", tags=["transactions"])


class TransactionCreate(BaseModel):
    amount: Decimal
    description: str | None = None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    transaction_type: str
    amount: Decimal
    timestamp: datetime
    description: str | None


def get_account(db: Session, account_id: int) -> Account:
    account = db.get(Account, account_id)

    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    return account


@router.post("/{account_id}/deposit", response_model=TransactionOut)
def deposit(account_id: int, request: TransactionCreate, db: Session = Depends(get_db)):
    if request.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Deposit amount must be greater than zero"
        )

    account = get_account(db, account_id)

    if account.status != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Account is {account.status} and cannot accept deposits"
        )

    account.balance += request.amount

    transaction = Transaction(
        account_id=account_id,
        transaction_type="deposit",
        amount=request.amount,
        description=request.description,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


@router.post("/{account_id}/withdraw", response_model=TransactionOut)
def withdraw(account_id: int, request: TransactionCreate, db: Session = Depends(get_db)):
    if request.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Withdrawal amount must be greater than zero"
        )

    account = get_account(db, account_id)

    if account.status != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Account is {account.status} and cannot process withdrawals"
        )

    if request.amount > account.balance:
        raise HTTPException(
            status_code=400,
            detail="Insufficient funds"
        )

    account.balance -= request.amount

    transaction = Transaction(
        account_id=account_id,
        transaction_type="withdrawal",
        amount=request.amount,
        description=request.description,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return transaction


@router.get("/{account_id}/transactions", response_model=list[TransactionOut])
def get_account_transactions(account_id: int, db: Session = Depends(get_db)):
    get_account(db, account_id)

    return (
        db.query(Transaction)
        .filter(Transaction.account_id == account_id)
        .all()
    )
