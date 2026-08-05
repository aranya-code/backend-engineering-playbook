"""
Main application entry point for the Multi-Container Demo.
This module initializes the FastAPI application and includes routers.
"""
from fastapi import FastAPI
from routers.home import router as home_router
from routers.products import router as product_router
from routers.tasks import router as task_router

app=FastAPI(title="Multi-Container Demo")
app.include_router(home_router)
app.include_router(product_router)
app.include_router(task_router)

@app.get("/health")
def health():
    # Simple health check endpoint used by Docker healthchecks
    return {"status":"healthy"}
