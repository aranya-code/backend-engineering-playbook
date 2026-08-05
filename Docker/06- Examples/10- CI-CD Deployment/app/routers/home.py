"""
Home router module.

Provides endpoints that return information about the application,
its environment, and its deployment details.
"""
import platform
from fastapi import APIRouter
from settings import APP_NAME,ENVIRONMENT,PIPELINE,VERSION

router=APIRouter()

# Return details about the application state and deployment pipeline
@router.get("/")
def home():
    return {
        "application":APP_NAME,
        "status":"Running",
        "environment":ENVIRONMENT,
        "pipeline":PIPELINE,
        "version":VERSION,
        "python_version":platform.python_version(),
        "hostname":platform.node()
    }
