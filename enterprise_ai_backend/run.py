"""Start the server. Usage: python run.py"""
import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
RELOAD = os.getenv("RELOAD", "true").lower() == "true"

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=RELOAD)
