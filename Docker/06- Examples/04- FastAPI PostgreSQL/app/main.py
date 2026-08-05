"""
Main FastAPI application file.
Sets up the web application, mounts static files, includes routers,
and initializes the database tables on startup.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database import Base, engine
from routers.home import router

# Create database tables based on SQLAlchemy models
Base.metadata.create_all(bind=engine)

# Initialize the FastAPI application
app = FastAPI(title="FastAPI + PostgreSQL")

# Mount static files directory for serving assets (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API endpoints from the router
app.include_router(router)
