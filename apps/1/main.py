"""Entry point for uvicorn."""
import os
from src.main import app

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))

    uvicorn.run(
        app,
        host=host,
        port=port,
    )
