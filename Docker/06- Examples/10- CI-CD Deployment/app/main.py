"""
Main application module.

This module initializes the FastAPI application and includes the routers.
It also provides a health check endpoint for monitoring.
"""
from fastapi import FastAPI
from routers.home import router

# Initialize the FastAPI app with a title
app=FastAPI(title="CI/CD Deployment Demo")

# Include the home router for standard endpoints
app.include_router(router)

# Health check endpoint used by Docker healthchecks
@app.get("/health")
def health():
    return {"status":"healthy"}
