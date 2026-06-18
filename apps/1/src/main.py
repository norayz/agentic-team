from fastapi import FastAPI
from src.routes import router
from src import database

app = FastAPI(
    title="Todo API",
    description="A simple todo management REST API",
    version="1.0.0"
)


@app.on_event("startup")
def startup():
    """Initialize database on startup"""
    database.init_db()


app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Todo API is running. Visit /docs for API documentation."}
