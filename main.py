from fastapi import FastAPI

from routers import test, transactions, users

app = FastAPI()

app.include_router(test.router)
app.include_router(transactions.router)
app.include_router(users.router)

@app.get("/")
def root():
    return {"message": "Banking API is running"}
