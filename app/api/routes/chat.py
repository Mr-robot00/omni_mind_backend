from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
import jwt
from pydantic import BaseModel
from app.models.user import DBUser
from app.api.routes.users import get_current_user
from app.gen_ai import llm, vector_store
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.security import SECRET_KEY, ALGORITHM
from sqlalchemy.orm import Session
from app.core.database import get_db




router = APIRouter()
async def get_current_user_ws(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        user = db.query(DBUser).filter(DBUser.email == email).first()
        return user
    except Exception:
        return None

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
@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time AI typing effects.
    Client connects with: ws://your-url/api/v1/ai/ws/chat?token=YOUR_JWT_TOKEN
    """
    await websocket.accept()
    
    # 1. Authenticate the user securely
    user = await get_current_user_ws(token, db)
    if not user:
        await websocket.send_json({"error": "Authentication failed"})
        await websocket.close(code=1008)
        return

    try:
        # Keep connection open to receive multiple messages
        while True:
            # Wait for user to send a message over the websocket
            data = await websocket.receive_text()
            
            # 2. RETRIEVAL: Find relevant memories
            results = vector_store.similarity_search(
                data,
                k=3,
                filter={"user_id": user.id} 
            )

            context_text = "\n\n".join([doc.page_content for doc in results])
            sources = [doc.metadata.get("title", "Unknown") for doc in results]
            
            # Send sources back instantly so the UI can show them before the AI types
            await websocket.send_json({"type": "sources", "data": list(set(sources))})

            system_prompt = f"""You are OmniMind, a secure AI assistant.
            Answer the user's question using ONLY the provided memories from their secure vault.
            If the answer is not in the memories, politely say "I cannot find information about that in your vault."

            VAULT MEMORIES:
            {context_text}
            """

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=data)
            ]

            # 3. GENERATION: Stream from Gemini word-by-word
            # using astream() which is an async generator
            async for chunk in llm.astream(messages):
                # Send each piece of the word back to the Flutter app instantly
                await websocket.send_json({
                    "type": "stream",
                    "data": chunk.content
                })
            
            # Tell the client the AI is done typing
            await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        print(f"Client {user.email} disconnected.")
    except Exception as e:
        print(f"WS Error: {e}")
        await websocket.close()