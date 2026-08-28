import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from routers import accounts, auth, test, transactions, transfers, users

app = FastAPI(
    title="Banking API",
    description="REST API for the banking application",
    version="1.0.0",
)

frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        frontend_origin,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(test.router)
app.include_router(transactions.router)
app.include_router(users.router)
app.include_router(accounts.router)
app.include_router(transfers.router)
app.include_router(auth.router)


@app.get("/")
def root():
    return {"message": "Banking API is running"}


handler = Mangum(app)
