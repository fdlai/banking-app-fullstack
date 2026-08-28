from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import accounts, test, transactions, transfers, users, auth

app = FastAPI(
    title="Banking API",
    description="REST API for the banking application",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://d3lcfu6nt18a65.cloudfront.net"],
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
app.include_router(users.router)

@app.get("/")
def root():
    return {"message": "Banking API is running"}
