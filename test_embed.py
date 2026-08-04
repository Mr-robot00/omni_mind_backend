import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

try:
    print("Testing text-embedding-004...")
    embeddings = GoogleGenerativeAIEmbeddings(model="text-embedding-004")
    res = embeddings.embed_query("Hello world")
    print(f"Success! Vector length: {len(res)}")
except Exception as e:
    print(f"Error with text-embedding-004: {e}")

try:
    print("Testing models/text-embedding-004...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    res = embeddings.embed_query("Hello world")
    print(f"Success! Vector length: {len(res)}")
except Exception as e:
    print(f"Error with models/text-embedding-004: {e}")

try:
    print("Testing embedding-001...")
    embeddings = GoogleGenerativeAIEmbeddings(model="embedding-001")
    res = embeddings.embed_query("Hello world")
    print(f"Success! Vector length: {len(res)}")
except Exception as e:
    print(f"Error with embedding-001: {e}")
