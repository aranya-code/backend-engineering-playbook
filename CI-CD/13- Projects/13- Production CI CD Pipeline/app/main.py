from fastapi import FastAPI

app = FastAPI(title="Production CI/CD Lab")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/version")
def version():
    return {"version": "0.1.0"}
