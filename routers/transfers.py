from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import NUMERIC, Column, Integer, String, Numeric, DateTime, ForeignKey

from database import get_db
from models.account import Account
from models.transactions import Transaction
from models.transfers import Transfer


router = APIRouter()

class TransferRequest(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: Decimal


@router.post("/transfers")
def create_transfer(request: TransferRequest, db: Session = Depends(get_db)):

    from_account = db.get(Account, request.from_account_id)

    if from_account is None:
        raise HTTPException(status_code=404, detail="From account not found" )


    to_account = db.get(Account, request.to_account_id)

    if to_account is None:
        raise HTTPException(status_code=404, detail="To account not found" )


    if from_account.status != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Account is {from_account.status} and cannot process transfers"
        )

    if to_account.status != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Account is {to_account.status} and cannot process transfers"
        )

    if to_account.id == from_account.id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account" )

    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Transfer amount must be greater than zero" )

    if from_account.balance < request.amount:
        raise HTTPException( status_code=400, detail="Insufficient funds" )

    #Actual Transfer
    from_account.balance -= request.amount
    to_account.balance += request.amount

    # Create send transaction
    send = Transaction(
        account_id=from_account.id,
        transaction_type="send",
        amount=request.amount,
        timestamp=datetime.now(timezone.utc),
        description=f"Transfer to account {to_account.id}"
    )

    # Create receive transaction
    receive = Transaction(
        account_id=to_account.id,
        transaction_type="receive",
        amount=request.amount,
        timestamp=datetime.now(timezone.utc),
        description=f"Transfer from account {from_account.id}"
    )

    db.add(send)
    db.add(receive)

    # Create transfer record
    transfer = Transfer(
        from_account_id=from_account.id,
        to_account_id=to_account.id,
        amount=request.amount,
        timestamp=datetime.now(timezone.utc),
        status="completed"
    )

    db.add(transfer)

    # Save everything
    db.commit()

    # Get the generated transfer ID
    db.refresh(transfer)

    return transfer
