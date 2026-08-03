from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import jwt

from app.core.database import get_db
from app.core.security import get_password_hash, oauth2_scheme, SECRET_KEY, ALGORITHM
from app.models.user import DBUser
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()

# --- Dependency to get current user (Moved here for route access) ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
        
    user = db.query(DBUser).filter(DBUser.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# --- Routes ---
@router.get("/", response_model=list[UserResponse])
def read_root(db: Session = Depends(get_db)):
    return db.query(DBUser).all()

@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(DBUser).filter(DBUser.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = get_password_hash(user.password)
    db_user = DBUser(name=user.name, email=user.email, hashed_password=hashed_pw, is_active=user.is_active)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: DBUser = Depends(get_current_user)):
    return current_user