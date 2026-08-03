import os
from fastapi import FastAPI, Depends, HTTPException,status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from datetime import datetime , timedelta , timezone
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import bcrypt
from app.core.database import engine, Base
from app.api.routes import auth, users
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from passlib.context import CryptContext
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_chroma import Chroma
from langchain_core.documents import Document
from fastapi import FastAPI, HTTPException, UploadFile, File
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.models.user import DBUser 
load_dotenv()

app = FastAPI(title="OmniMind API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------

# Create database tables
Base.metadata.create_all(bind=engine)
# # --- AI CORE SETUP ---  

# # 1. The Brain (Generation)
# llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

# # 2. The Translator (Embeddings)
# # This converts text into mathematical vectors
# # Change this line in your main.py:
# embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
# # 3. The Memory (Vector Database)
# # We store the data locally in a folder named "vault_db"
# vector_store = Chroma(
#     collection_name="user_vault",
#     embedding_function=embeddings,
#     persist_directory="./vault_db"
# )
# text_splitter = RecursiveCharacterTextSplitter(
#     chunk_size=500,       # Maximum characters per chunk
#     chunk_overlap=50,     # Repeat 50 characters between chunks to preserve context
#     separators=["\n\n", "\n", " ", ""] # Try splitting by paragraphs first, then sentences, then words
# )
# # --- DATA MODELS ---

# class QueryRequest(BaseModel):
#     text: str

# class IngestRequest(BaseModel):
#     document_text: str
#     source_name: str

# # --- ENDPOINTS ---

# @app.post("/api/ingest/file")
# async def memorize_file(file: UploadFile = File(...)):
#     """Accepts a physical file upload, reads the content, chunks it, and vectorizes it."""
#     try:
#         # A. Read raw bytes and decode to string (handles .txt, .md, .csv, etc.)
#         content_bytes = await file.read()
#         try:
#             document_text = content_bytes.decode("utf-8")
#         except UnicodeDecodeError:
#             raise HTTPException(status_code=400, detail="Only UTF-8 text files (.txt, .md, .csv) are currently supported.")
        
#         # B. Use our Smart Splitter from Step 1 to slice the document
#         chunks = text_splitter.split_text(document_text)
        
#         docs = [
#             Document(
#                 page_content=chunk,
#                 metadata={
#                     "source": file.filename,   # Automatically use the uploaded file's name!
#                     "chunk_index": i,
#                     "total_chunks": len(chunks)
#                 }
#             )
#             for i, chunk in enumerate(chunks)
#         ]
        
#         # D. Save to local ChromaDB memory
#         vector_store.add_documents(docs)
        
#         return {
#             "status": "success", 
#             "message": f"Successfully memorized {len(docs)} chunks from file: {file.filename}"
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
        
# @app.post("/api/chat")
# async def chat_with_ai(request: QueryRequest):
#     user_text = request.text
    
#     try:
#         # 1. RETRIEVAL: Search the database for relevant chunks
#         # Fetch the top 3 most relevant memories based on the user's question
#         relevant_docs = vector_store.similarity_search(user_text, k=3)
        
#         # 2. AUGMENTATION: Combine retrieved text into a single context string
#         context_string = "\n\n".join([doc.page_content for doc in relevant_docs])
#         sources = [doc.metadata.get("source", "Unknown") for doc in relevant_docs]
        
#         # 3. GENERATION: Instruct Gemini to use the context
#       # 3. GENERATION: Smart context-aware instructions
#         system_prompt = f"""You are OmniMind, an intelligent and helpful personal assistant with access to the user's private memory vault.
        
#         HERE ARE RETRIEVED MEMORIES FROM THE VAULT:
#         {context_string}
        
#         INSTRUCTIONS:
#         1. If the user is asking a factual question, answer it using ONLY the retrieved memories above. 
#         2. If the retrieved memories do not contain the answer to a factual question, politely state: "I don't have that information in my vault memories."
#         3. If the user is just saying hello, chatting casually, or asking general knowledge questions not requiring private data, respond naturally and conversationally without forcing the memories into the chat.
#         """
        
#         messages = [
#             SystemMessage(content=system_prompt),
#             HumanMessage(content=user_text)
#         ]
        
#         response = llm.invoke(messages)
        
#         return {
#             "status": "success",
#             "answer": response.content,
#             # We return the sources so the Flutter UI can display citation chips
#             "sources": list(set(sources)) 
#         }
        
#     except Exception as e:
#         return {
#             "status": "error",
#             "answer": f"Core processing error: {str(e)}",
#             "sources": []
#         }

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])