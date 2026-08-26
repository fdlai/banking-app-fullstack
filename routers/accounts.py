# /routers/accounts.py
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models.account import Account
from models.user import User

router = APIRouter(prefix="/accounts", tags=["accounts"])


class AccountCreate(BaseModel):
    user_id: UUID
    account_type: str
    status: str


@router.get("")
def get_accounts(db: Session = Depends(get_db)):
    accounts = db.scalars(select(Account)).all()

    return accounts


@router.get("/{account_id}")
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
):
    account = db.get(Account, account_id)

    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    return account


@router.post("", status_code=status.HTTP_201_CREATED)
def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
):
    user = db.get(User, account.user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    new_account = Account(
        user_id=account.user_id,
        account_type=account.account_type,
        balance=Decimal("0.00"),
        status=account.status,
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return new_account
