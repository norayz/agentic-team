from fastapi import FastAPI
from src.database import init_db
from src.routes import router

app = FastAPI(
    title="Todo API",
    description="A simple personal todo REST API",
    version="1.0.0",
)


@app.on_event("startup")
def startup_event():
    """Initialize database on app startup."""
    init_db()


app.include_router(router)
