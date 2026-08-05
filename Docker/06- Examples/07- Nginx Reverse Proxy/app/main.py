"""
Main Application Module.

This module initializes the FastAPI application, sets up a health check endpoint,
and includes the routing configuration for the application.
"""
from fastapi import FastAPI
from routers.home import router

# Initialize the FastAPI application
app = FastAPI(title="FastAPI Behind Nginx")

# Define a health check endpoint used by Docker Healthcheck
@app.get("/health")
def health():
    return {"status":"healthy"}

# Include external routers to keep the main file clean
app.include_router(router)
