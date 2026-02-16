# cmp_document_chat/backend/app/services/document_service.py

import os
import glob
import openai
# Import PyPDF2
from pypdf import PdfReader # PyPDF2 is now pypdf, use PdfReader
import markdown # Assuming you'll use markdown files primarily for now

class DocumentService:
    def __init__(self, docs_path: str):
        self.docs_path = docs_path
        self.documents_content = {} # Store content of loaded documents
        self.loaded_files = []      # Keep track of loaded file names
        print(f"DocumentService initialized with path: {self.docs_path}")

        import asyncio
        asyncio.run(self.load_and_index_documents())

    async def load_and_index_documents(self):
        """
        Loads all documents (.md, .pdf) from the specified path and prepares them.
        """
        self.documents_content = {}
        self.loaded_files = []
        print(f"Scanning for documents in: {self.docs_path}")

        # --- Handle Markdown Files ---
        for filepath in glob.glob(os.path.join(self.docs_path, "*.md")):
            filename = os.path.basename(filepath)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.documents_content[filename] = content
                    self.loaded_files.append(filename)
                    print(f"Loaded Markdown: {filename}")
            except Exception as e:
                print(f"Error reading Markdown file {filename}: {e}")

        # --- Handle PDF Files ---
        for filepath in glob.glob(os.path.join(self.docs_path, "*.pdf")):
            filename = os.path.basename(filepath)
            try:
                reader = PdfReader(filepath)
                content = ""
                for page in reader.pages:
                    content += page.extract_text() + "\n" # Append text from each page
                
                if content.strip(): # Only add if text was actually extracted
                    self.documents_content[filename] = content
                    self.loaded_files.append(filename)
                    print(f"Loaded PDF: {filename}")
                else:
                    print(f"No text extracted from PDF: {filename}")

            except Exception as e:
                print(f"Error reading PDF file {filename}: {e}")

        # Add logic here for other file types like .docx if needed

        if not self.documents_content:
            print("No documents found or loaded.")
        else:
            print(f"Successfully loaded {len(self.loaded_files)} document(s).")
            # print(f"Loaded file names: {self.loaded_files}") # For debugging


    async def get_answer(self, query: str) -> tuple[str, list[str] | None]:
        """
        Generates an answer to the query using OpenAI, augmented with document content.
        """
        if not self.documents_content:
            return "No documents are available to answer your query.", None

        # --- Basic Prompt Engineering ---
        full_context = "\n---\n".join(
            f"--- {filename} ---\n{content}"
            for filename, content in self.documents_content.items()
        )

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
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI assistant for Solution Architect that answers questions based on provided CMP documents. Be concise and informative."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7,
            )
            answer = response.choices[0].message.content.strip()

            # In a real RAG system, you'd also identify which source documents/chunks were most relevant
            # For this simple version, we'll list all loaded files as potential sources.
            sources = self.loaded_files if self.loaded_files else ["N/A"]

            return answer, sources

        except openai.APIError as e:
            print(f"OpenAI API error: {e}")
            raise e

        except Exception as e:
            print(f"An unexpected error occurred during OpenAI call: {e}")
            raise e

