# cmp_document_chat/backend/app/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Import your document service
from .services.document_service import DocumentService # We'll create this next

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

# Configure OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise EnvironmentError("OPENAI_API_KEY not found in environment variables.")

# Initialize the OpenAI client (using the new client structure)
# You might want to manage this client instance differently in a larger app,
# but this is fine for a start.
import openai
openai.api_key = openai_api_key

# Initialize the Document Service
# This is where you'd configure your document paths, embedding models, etc.
# For now, we'll point it to the 'docs/' directory relative to the project root.
# We need to know the project root. Let's assume backend/ is one level down from root.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
docs_path = os.path.join(project_root, "docs")
document_service = DocumentService(docs_path=docs_path)

# --- FastAPI App ---
app = FastAPI(
    title="CMP Document Chat API",
    description="API for querying CMP documents using OpenAI.",
    version="1.0.0",
)

# --- Models ---
class ChatRequest(BaseModel):
    query: str
    # Add optional parameters later, e.g., conversation_history, specific_document

class ChatResponse(BaseModel):
    answer: str
    source_documents: list[str] | None = None # To show which docs were used

# --- Endpoints ---
@app.get("/")
async def read_root():
    """A simple health check endpoint."""
    return {"message": "CMP Document Chat API is running!"}

@app.post("/chat/", response_model=ChatResponse)
async def chat_with_documents(request: ChatRequest):
    """
    Endpoint to query the CMP documents.
    Takes a user query and returns an AI-generated answer based on the documents.
    """
    user_query = request.query
    if not user_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    print(f"Received query: '{user_query}'") # Log the query

    try:
        # --- Integration Point ---
        # Here we'll call our document service to get relevant context and generate an answer
        answer, sources = await document_service.get_answer(user_query)

        return ChatResponse(answer=answer, source_documents=sources)

    except Exception as e:
        print(f"An error occurred: {e}") # Log the error
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")

# --- Optional: Endpoint to load/refresh documents ---
# This is useful if you update documents without redeploying.
@app.post("/documents/refresh/")
async def refresh_documents():
    """
    Endpoint to trigger a refresh/re-indexing of the documents.
    """
    try:
        await document_service.load_and_index_documents()
        return {"message": "Documents re-indexed successfully."}
    except Exception as e:
        print(f"Error during document refresh: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh documents: {str(e)}")

