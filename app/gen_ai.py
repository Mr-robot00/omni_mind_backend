import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
    print("🚨 WARNING: GOOGLE_API_KEY or GEMINI_API_KEY is missing from .env!")
if not os.getenv("PINECONE_API_KEY"):
    print("🚨 WARNING: PINECONE_API_KEY is missing from .env!")    

# 1. The Brain (Generative Model)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

# 2. The Translator (Embeddings)
# Changed to embedding-001 to force exactly 768 dimensions!
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# 3. The Memory (Cloud Vector Database)
index_name = "vault" 

vector_store = PineconeVectorStore(
    index_name=index_name, 
    embedding=embeddings
)