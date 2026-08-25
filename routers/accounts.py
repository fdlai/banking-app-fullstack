from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from data.mock_data import accounts, users

router = APIRouter(prefix="/accounts", tags=["accounts"])


class AccountCreate(BaseModel):
    user_id: int
    account_type: str
    status: str


@router.get("")
def get_accounts():
    return accounts


@router.get("/{account_id}")
def get_account(account_id: int):
    for account in accounts:
        if account["id"] == account_id:
            return account

    raise HTTPException(
        status_code=404,
        detail="Account not found"
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_account(account: AccountCreate):
    user_exists = any(user["id"] == account.user_id for user in users)

    if not user_exists:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    new_id = max(a["id"] for a in accounts) + 1 if accounts else 1

    new_account = {
        "id": new_id,
        "user_id": account.user_id,
        "account_type": account.account_type,
        "balance": 0.0,
        "status": account.status,
    }

    accounts.append(new_account)

    return new_account