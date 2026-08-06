from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.vault import DBVaultItem
from app.models.user import DBUser
from app.schemas.vault import VaultItemCreate, VaultItemResponse
from app.api.routes.users import get_current_user 
from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File, HTTPException, status
import io
import PyPDF2

# --- ADD THIS NEW IMPORT ---
from app.services.tasks import process_pdf_task
# -----------------------------

from app.core.ai import vector_store
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import uuid
# -----------------------------

router = APIRouter()

# --- NEW HELPER FUNCTION ---
def vectorize_vault_item_background(title: str, secret_content: str, user_id: int):
    """
    This function runs AFTER the user gets their success response.
    It handles the slow API call to Google to generate embeddings.
    """
    try:
        doc = Document(
            page_content=f"Topic: {title}\nDetails: {secret_content}",
            metadata={
                "user_id": user_id, 
                "title": title
            },
            id=str(uuid.uuid4())
        )
        vector_store.add_documents([doc])
        print(f"✅ Background Task: Successfully vectorized vault item for user {user_id}")
    except Exception as e:
        print(f"🚨 Background Task Error: Failed to vectorize item. Error: {e}")

# We are removing process_and_vectorize_file_background completely from this file!
# It has been moved to app/services/tasks.py to run in the Celery Worker.

@router.post("/", response_model=VaultItemResponse)
def create_vault_item(
    item: VaultItemCreate, 
    background_tasks: BackgroundTasks, # <-- ADD THIS PARAMETER
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """
    Creates a new vault item and automatically assigns it to the logged-in user.
    """
    db_item = DBVaultItem(
        title=item.title,
        secret_content=item.secret_content,
        user_id=current_user.id
    )
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # --- AI INTEGRATION: SAVE TO VECTOR MEMORY IN BACKGROUND ---
    # Instead of blocking the user, we hand the job to FastAPI's background worker
    background_tasks.add_task(
        vectorize_vault_item_background, 
        title=item.title, 
        secret_content=item.secret_content, 
        user_id=current_user.id
    )
    # ---------------------------------------------

    return db_item

@router.get("/", response_model=list[VaultItemResponse])
def get_my_vault_items(
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user) # 🛑 SECURE: Identifies the user
):
    """
    Fetches ONLY the vault items belonging to the user making the request.
    """
    # 🛡️ The Filter: DBVaultItem.user_id == current_user.id
    # This guarantees no one can read someone else's data.
    items = db.query(DBVaultItem).filter(DBVaultItem.user_id == current_user.id).all()
    
    return items

# --- UPDATED ENDPOINT FOR FILE UPLOADS ---
@router.post("/upload")
async def upload_vault_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """
    Accepts a PDF or TXT file, creates a record in Postgres, and kicks off a 
    CELERY task to vectorize its contents in a separate worker process.
    """
    # 1. Validate file extension early
    allowed_extensions = [".pdf", ".txt", ".md"]
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF, TXT, and MD files are supported right now."
        )

    # 2. Read the file into memory
    file_content = await file.read()

    # 3. Save a record in PostgreSQL so the user sees it in their Vault list
    db_item = DBVaultItem(
        title=f"File: {file.filename}",
        secret_content=f"[Content extracted and stored in AI memory]", 
        user_id=current_user.id
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # 4. Hand the heavy lifting to CELERY!
    # We must convert bytes to hex because Celery uses JSON for the queue, 
    # and JSON cannot hold raw binary byte data.
    file_content_hex = file_content.hex()
    
    # .delay() puts the task in the Redis queue instantly.
    process_pdf_task.delay(
        file_content_hex=file_content_hex, 
        filename=file.filename, 
        user_id=current_user.id
    )

    return {
        "status": "success",
        "message": f"File {file.filename} queued for processing by worker.",
        "vault_id": db_item.id
    }
# -------------------------------------

def delete_vector_item_background(user_id: int, title: str):
@router.delete("/{item_id}")
def delete_vault_item(
    item_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    """
    Deletes a vault item from PostgreSQL AND removes its vectors from Pinecone.
    """
    # 1. Find the item in Postgres (and make sure it belongs to the logged-in user!)
    db_item = db.query(DBVaultItem).filter(
        DBVaultItem.id == item_id, 
        DBVaultItem.user_id == current_user.id
    ).first()

    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found or you don't have permission to delete it."
        )

    # 2. Save the title so we can tell Pinecone what to delete
    title_to_delete = db_item.title

    # 3. Delete from PostgreSQL
    db.delete(db_item)
    db.commit()

    # 4. Hand the Pinecone deletion to a background task so the API is fast
    background_tasks.add_task(
        delete_vector_item_background,
        user_id=current_user.id,
        title=title_to_delete
    )

    return {
        "status": "success",
        "message": f"Item '{title_to_delete}' has been permanently deleted from the Vault and AI memory."
    }
# ---------------------------