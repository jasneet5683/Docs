# cmp_document_chat/backend/uvicorn_config.py
import os

workers = 1
# Set host and port from environment variables, defaulting to 0.0.0.0:8000
host = os.getenv("HOST", "0.0.0.0")
port = int(os.getenv("PORT", 8000))

# bind = f"{host}:{port}" # Uvicorn v0.13.0+ uses this format
