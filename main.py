from fastapi import FastAPI

from routers import accounts, test, transactions, transfers, users

app = FastAPI(
    title="Banking API",
    description="REST API for the banking application",
    version="1.0.0",
)

app.include_router(test.router)
app.include_router(transactions.router)
app.include_router(users.router)
app.include_router(accounts.router)
app.include_router(transfers.router)


@app.get("/")
def root():
    return {"message": "Banking API is running"}
