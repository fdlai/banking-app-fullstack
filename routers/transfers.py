from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone

router = APIRouter()


from data.mock_data import accounts, transfers, transactions
from routers.transactions import get_account, record_transaction


class TransferRequest(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float


@router.post("/transfers")
def create_transfer(request: TransferRequest):

    from_account = None
    for account in accounts:
        if account["id"] == request.from_account_id:
            from_account = account
            break
    if from_account is None:
        raise HTTPException(status_code=404, detail="From account not found" )


    to_account = None
    for account in accounts:
        if account["id"] == request.to_account_id:
            to_account = account
            break
    if to_account is None:
        raise HTTPException(status_code=404, detail="To account not found" )


    if from_account["status"] != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Account is {from_account['status']} and cannot process withdrawals"
        )

    if to_account["status"] != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Account is {to_account['status']} and cannot process withdrawals"
        )

    if to_account["id"] == from_account["id"]:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account" )

    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Transfer amount must be greater than zero" )

    if from_account["balance"] < request.amount:
        raise HTTPException( status_code=400, detail="Insufficient funds" )

    #Actual Transfer
    from_account["balance"] -= request.amount
    to_account["balance"] += request.amount

    #Record Transactions (From)
    record_transaction(
        request.from_account_id,
        "withdrawal",
        request.amount,
        f"Transfer to account {request.to_account_id}"
    )

    #Record Transactions (To)
    record_transaction(
        request.to_account_id,
        "deposit",
        request.amount,
        f"Transfer from account {request.from_account_id}"
    )

    #Record
    transfer = {
        "id": len(transfers) + 1,
        "from_account_id": request.from_account_id,
        "to_account_id": request.to_account_id,
        "amount": request.amount,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "completed"
    }

    transfers.append(transfer)

    return transfer
