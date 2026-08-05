from fastapi import FastAPI
from routers.products import router

app = FastAPI(title="FastAPI + Redis")

@app.get("/health")
def health():
    return {"status":"healthy"}

app.include_router(router)
