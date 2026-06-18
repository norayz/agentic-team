import os
import uvicorn
from src.main import app

if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=os.getenv("APP_ENV", "development") == "development",
    )
