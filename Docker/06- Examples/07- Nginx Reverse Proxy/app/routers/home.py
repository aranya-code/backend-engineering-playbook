"""
Home Router Module.

Provides the primary routing endpoints for the application.
"""
import platform
from fastapi import APIRouter

# Initialize the router instance
router = APIRouter()

# Define the root endpoint
@router.get("/")
def home():
    # Return information about the host serving the request
    return {
        "message":"Hello from FastAPI!",
        "served_by":"FastAPI",
        "hostname":platform.node(),
        "python_version":platform.python_version()
    }
