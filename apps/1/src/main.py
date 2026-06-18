"""FastAPI application factory."""
from fastapi import FastAPI
from src import database
from src import routes

app = FastAPI(
    title="Todo API",
    description="A simple REST API for managing todo items",
    version="1.0.0"
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    try:
        database.init_db()
    except RuntimeError as e:
        raise RuntimeError(f"Failed to initialize database on startup: {e}")

# Include routes
app.include_router(routes.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Todo API is running. Visit /docs for API documentation."}
