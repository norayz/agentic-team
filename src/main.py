"""FastAPI application entry point."""
from fastapi import FastAPI
from src.database import init_db
from src.routes import router

# Initialize FastAPI app
app = FastAPI(
    title="Todo API",
    description="A simple REST API for managing todo items",
    version="1.0.0",
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    """Initialize database on application startup."""
    init_db()


# Include routes
app.include_router(router)


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Welcome to the Todo API. Visit /docs for API documentation."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
