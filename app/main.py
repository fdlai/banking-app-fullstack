from fastapi import FastAPI

from app.routers import users

app = FastAPI(title="Bank API", version="0.1.0")
app.include_router(users.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}