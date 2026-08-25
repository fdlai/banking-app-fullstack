from fastapi import FastAPI

from routers import test, transactions

app = FastAPI(
    title="Banking API",
    description="REST API for the banking application",
    version="1.0.0",
)

app.include_router(test.router)
app.include_router(transactions.router)


@app.get("/")
def root():
    return {"message": "Banking API is running"}
