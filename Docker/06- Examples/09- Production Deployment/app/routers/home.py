"""
Home router module.
Provides the root endpoint displaying application metadata.
"""
import platform
from fastapi import APIRouter
from settings import APP_NAME,ENVIRONMENT,VERSION

router=APIRouter()

@router.get("/")
def home():
    # Returns application metadata, including the current hostname 
    # to demonstrate load balancing or container identity.
    return {
        "application":APP_NAME,
        "status":"Production Ready",
        "environment":ENVIRONMENT,
        "version":VERSION,
        "python_version":platform.python_version(),
        "hostname":platform.node()
    }
