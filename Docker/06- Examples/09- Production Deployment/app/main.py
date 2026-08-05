"""
Main application module.
Initializes the FastAPI application and includes the API routers.
"""
from fastapi import FastAPI
from routers.home import router

app=FastAPI(title="Production Deployment Demo")

# Include the home router for the main endpoints
app.include_router(router)

@app.get("/health")
def health():
    # Simple health check endpoint used by Docker or load balancers
    return {"status":"healthy"}
