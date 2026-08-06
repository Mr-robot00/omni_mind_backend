import os
import uuid
import io
import PyPDF2
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Import our new Celery configuration
from app.core.celery_app import celery
# Import our AI components
from app.gen_ai import vector_store

@celery.task(name="process_pdf_task")
def process_pdf_task(file_content_hex: str, filename: str, user_id: int):
    """
    This function runs entirely in a separate worker process, managed by Celery.
    It takes the heavy lifting off the FastAPI server.
    """
    print(f"🚀 Worker started processing file: {filename} for user {user_id}")
    
    try:
        # 1. We must decode the hex back into bytes because Celery requires
        # all data passed to it to be JSON serializable (bytes are not).
        file_content = bytes.fromhex(file_content_hex)
        extracted_text = ""
        
        # 2. Extract Text
        if filename.endswith(".pdf"):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
        elif filename.endswith(".txt") or filename.endswith(".md"):
            extracted_text = file_content.decode("utf-8")
        else:
            return {"status": "error", "message": f"Unsupported file type: {filename}"}

        if not extracted_text.strip():
            return {"status": "error", "message": "No text extracted."}

        # 3. Chunk the Text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_text(extracted_text)

        # 4. Create Documents and Vectorize
        documents = []
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "user_id": user_id,
                    "title": filename,
                    "chunk_index": i
                },
                id=str(uuid.uuid4())
            )
            documents.append(doc)

        # The actual heavy API call to Pinecone and Google
        vector_store.add_documents(documents)
        
        print(f"✅ Worker successfully vectorized {len(documents)} chunks from {filename}")
        return {"status": "success", "chunks_processed": len(documents)}

    except Exception as e:
        print(f"🚨 Worker Error processing file {filename}. Error: {e}")
        return {"status": "error", "message": str(e)}