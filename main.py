from fastapi import FastAPI

from routers import test, accounts

app = FastAPI()

app.include_router(test.router)
app.include_router(accounts.router)


@app.get("/")
def root():
    return {"message": "Banking API is running"}
