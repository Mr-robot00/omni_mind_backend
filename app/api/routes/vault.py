from ast import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.vault import DBVaultItem
from app.models.user import DBUser
from app.schemas.vault import VaultItemResponse, VaultItemCreate

from app.api.routes.users import get_current_user

router = APIRouter()

@router.post("/", response_model = VaultItemResponse)
def create_vault_item(
    item:VaultItemCreate,
    db:Session = Depends(get_db),
    current_user:DBUser = Depends(get_current_user)):
    """
    Creates a new vault item and automatically assigns it to the logged-in user.
    Flutter only needs to send 'title' and 'secret_content'.
    """
    db_item = DBVaultItem(
        title = item.title,
        secret_content = item.secret_content,
        user_id = current_user.id
    ) 
    db.add(db_item)
    db.commit()
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

