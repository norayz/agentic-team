"""FastAPI application factory."""

from fastapi import FastAPI
from src.database import Database
from src.routes import router, set_database


def create_app(db_path: str = None) -> FastAPI:
    """Create and configure FastAPI application.
    
    Args:
        db_path: Path to SQLite database file. If None, uses DATABASE_URL
                environment variable or defaults to 'todos.db'.
    
    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Todo API",
        description="Simple REST API for managing todo items",
        version="1.0.0",
    )

    # Initialize database
    db = Database(db_path=db_path)
    set_database(db)

    # Include routes
    app.include_router(router)

    @app.get("/")
    def root():
        """Root endpoint."""
        return {"message": "Todo API is running. Visit /docs for API documentation."}

    return app
