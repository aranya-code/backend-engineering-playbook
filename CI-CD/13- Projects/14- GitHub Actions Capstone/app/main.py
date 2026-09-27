import os
from fastapi import FastAPI

app = FastAPI(title="GitHub Actions Capstone")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/config")
def config():
    return {"environment": os.getenv("APP_ENV", "local")}
