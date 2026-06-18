"""FastAPI application entry point."""
from fastapi import FastAPI
from src.routes import router

app = FastAPI(
    title="Todo API",
    description="A simple REST API for managing todo items",
    version="1.0.0",
)

# Include routes
app.include_router(router)


@app.get("/")
def read_root():
    """Root endpoint with API information."""
    return {
        "message": "Todo API",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }
