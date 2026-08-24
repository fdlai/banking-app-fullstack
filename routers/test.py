from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/test", tags=["test"])

account = {"id": 101, "owner": "Alice", "balance": 1000.00}


class DepositRequest(BaseModel):
    amount: float


@router.get("/account")
def get_account():
    return account


@router.post("/account/deposit")
def deposit(request: DepositRequest):
    if request.amount <= 0:
        raise HTTPException(
            status_code=400, detail="Deposit amount must be greater than zero"
        )

    account["balance"] += request.amount

    return account
