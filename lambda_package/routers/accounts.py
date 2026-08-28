# /routers/accounts.py

from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.dependencies import get_current_user
from database import get_db
from models.account import Account
from models.user import User
from schemas.user import UserOut, UserRole

router = APIRouter(prefix="/accounts", tags=["accounts"])


class AccountCreate(BaseModel):
    user_id: UUID
    account_type: Literal["checking", "savings"]


def require_staff(
    actor: UserOut = Depends(get_current_user),
) -> UserOut:
    if actor.role not in (UserRole.ADMIN, UserRole.TELLER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required",
        )

    return actor


def require_admin(
    actor: UserOut = Depends(get_current_user),
) -> UserOut:
    if actor.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return actor


def _get_account_or_404(db: Session, account_id: int) -> Account:
    account = db.get(Account, account_id)

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    return account



@router.get("/me")
def get_my_accounts(
    db: Session = Depends(get_db),
    actor: UserOut = Depends(get_current_user),
):
    accounts = db.scalars(
        select(Account).where(Account.user_id == actor.id)
    ).all()

    return accounts


@router.get("")
def get_accounts(
    db: Session = Depends(get_db),
    actor: UserOut = Depends(require_staff),
):
    accounts = db.scalars(select(Account)).all()

    return accounts


@router.get("/{account_id}")
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    actor: UserOut = Depends(get_current_user),
):
    account = db.get(Account, account_id)

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    # Admins and tellers can view any account.
    if actor.role in (UserRole.ADMIN, UserRole.TELLER):
        return account

    # Customers can only view their own account.
    if actor.role == UserRole.CUSTOMER and account.user_id == actor.id:
        return account

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not permitted to view this account",
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
    actor: UserOut = Depends(require_staff),
):
    user = db.get(User, account.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Accounts can only be created for customers",
        )

    new_account = Account(
        user_id=account.user_id,
        account_type=account.account_type,
        balance=Decimal("0.00"),
        status="active",
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return new_account


@router.patch("/{account_id}/freeze")
def freeze_account(
    account_id: int,
    db: Session = Depends(get_db),
    actor: UserOut = Depends(require_admin),
):
    account = _get_account_or_404(db, account_id)

    if account.status == "closed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot freeze a closed account",
        )

    account.status = "frozen"
    db.commit()
    db.refresh(account)

    return account


@router.patch("/{account_id}/unfreeze")
def unfreeze_account(
    account_id: int,
    db: Session = Depends(get_db),
    actor: UserOut = Depends(require_admin),
):
    account = _get_account_or_404(db, account_id)

    if account.status == "closed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unfreeze a closed account",
        )

    if account.status != "frozen":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is not frozen",
        )

    account.status = "active"
    db.commit()
    db.refresh(account)

    return account


