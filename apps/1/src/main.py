"""FastAPI application factory and configuration."""
from fastapi import FastAPI
from src.database import init_db
from src.routes import router

app = FastAPI(
    title="Todo API",
    description="A simple REST API for managing todo items",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


app.include_router(router)
