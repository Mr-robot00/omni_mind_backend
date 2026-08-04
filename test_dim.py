import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
res = embeddings.embed_query("Hello world")
print(f"Dimension of models/gemini-embedding-2 is: {len(res)}")
