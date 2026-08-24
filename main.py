from fastapi import FastAPI

app = FastAPI()


# Some test code to check if the API is running
@app.get("/")
def root():
    return {"message": "Banking API is running"}
