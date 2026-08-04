from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.models.user import DBUser
from app.api.routes.users import get_current_user
from app.gen_ai import llm, vector_store
from langchain_core.messages import SystemMessage, HumanMessage

router = APIRouter()

class ChatRequest(BaseModel):
    question: str

@router.post("/chat")
def chat_with_vault(
    request:ChatRequest,
    current_user:DBUser = Depends(get_current_user)):
    results = vector_store.similarity_search(
        request.question,
        k=3,
        filter={
            "user_id": current_user.id
        }
    )    
    context_text = "\n\n".join([doc.page_content for doc in results])
    sources = [doc.metadata.get("title", "Unknown") for doc in results]

    system_prompt = f"""You are OmniMind, a secure AI assistant.
    Answer the user's question using ONLY the provided memories from their secure vault.
    If the answer is not in the memories, politely say "I cannot find information about that in your vault." Do not use outside knowledge.

    VAULT MEMORIES:
    {context_text}
    """

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=request.question)
    ]

    response = llm.invoke(messages)

    return {
        "status": "success",
        "answer": response.content,
        "sources": list(set(sources)) # Returns the titles of the notes used!
    }