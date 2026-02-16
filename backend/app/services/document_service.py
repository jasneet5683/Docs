# cmp_document_chat/backend/app/services/document_service.py

import os
import glob
import openai
import markdown # Assuming you'll use markdown files primarily for now

class DocumentService:
    def __init__(self, docs_path: str):
        self.docs_path = docs_path
        self.documents_content = {} # Store content of loaded documents
        self.loaded_files = []      # Keep track of loaded file names
        print(f"DocumentService initialized with path: {self.docs_path}")
        # In a real RAG system, you'd initialize embedding models and vector stores here.
        # self.embedding_model = ...
        # self.vector_store = ...

        # Load documents on initialization
        # For a more robust system, you might want async loading or a separate trigger.
        import asyncio
        asyncio.run(self.load_and_index_documents())

    async def load_and_index_documents(self):
        """
        Loads all documents from the specified path and prepares them.
        For simplicity, this just reads their content.
        """
        self.documents_content = {}
        self.loaded_files = []
        print(f"Scanning for documents in: {self.docs_path}")

        # Find all markdown files (.md)
        for filepath in glob.glob(os.path.join(self.docs_path, "*.md")):
            filename = os.path.basename(filepath)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.documents_content[filename] = content
                    self.loaded_files.append(filename)
                    print(f"Loaded: {filename}")
            except Exception as e:
                print(f"Error reading {filename}: {e}")

        # You would add logic here to:
        # 1. Parse other file types (.pdf, .docx)
        # 2. Chunk the content
        # 3. Generate embeddings
        # 4. Store embeddings in a vector database

        if not self.documents_content:
            print("No documents found or loaded.")
        else:
            print(f"Successfully loaded {len(self.loaded_files)} document(s).")

    async def get_answer(self, query: str) -> tuple[str, list[str] | None]:
        """
        Generates an answer to the query using OpenAI, augmented with document content.
        This is a basic implementation. A true RAG would involve retrieving relevant chunks first.
        """
        if not self.documents_content:
            return "No documents are available to answer your query.", None

        # --- Basic Prompt Engineering ---
        # Combine all document contents into a single context string for simplicity.
        # THIS IS NOT SCALABLE FOR LARGE DOCUMENT SETS.
        # A real RAG system would retrieve only the MOST relevant chunks.
        full_context = "\n---\n".join(
            f"--- {filename} ---\n{content}"
            for filename, content in self.documents_content.items()
        )

        # Craft a prompt that includes the context and the user's question
        prompt = f"""You are an AI assistant that answers questions based on the provided CMP documents.
        Use the following document content to answer the question. If you cannot find the answer in the documents, say "I could not find the answer in the provided documents."
        Do not make up information.

        Documents:
        {full_context}

        User Question: {query}

        Answer:
        """

        print(f"Sending prompt to OpenAI (length: {len(prompt)} characters)...")

        try:
            # Using the newer OpenAI client API structure
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",  # Or "gpt-4" for better quality but higher cost
                messages=[
                    {"role": "system", "content": "You are an AI assistant that answers questions based on provided CMP documents. Be concise and informative."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500, # Adjust as needed
                temperature=0.7, # Adjust for creativity vs. factuality
            )
            answer = response.choices[0].message.content.strip()

            # In a real RAG system, you'd also identify which source documents/chunks were most relevant
            # For this simple version, we'll list all loaded files as potential sources.
            sources = self.loaded_files if self.loaded_files else ["N/A"]

            return answer, sources

        except openai.APIError as e:
            print(f"OpenAI API error: {e}")
            raise e # Re-raise to be caught by FastAPI HTTPException

        except Exception as e:
            print(f"An unexpected error occurred during OpenAI call: {e}")
            raise e

