"""Entry point for uvicorn server."""

import os
from src.main import create_app

# Create FastAPI app
app = create_app()

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
    )
