from fastapi import FastAPI

from routers import test, transactions

app = FastAPI()

app.include_router(test.router)
app.include_router(transactions.router)


@app.get("/")
def root():
    return {"message": "Banking API is running"}
