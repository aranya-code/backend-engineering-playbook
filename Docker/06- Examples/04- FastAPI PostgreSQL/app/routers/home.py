import os, platform
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router=APIRouter()

@router.get("/", response_class=HTMLResponse)
def home():
    return f"<h1>{os.getenv('APP_NAME')}</h1><p>FastAPI is running inside Docker.</p><ul><li>Database: {os.getenv('POSTGRES_DB')}</li><li>Hostname: {platform.node()}</li><li>Python: {platform.python_version()}</li></ul>"

@router.get("/health")
def health():
    return {"status":"healthy"}
