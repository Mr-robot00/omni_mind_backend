from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base

class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String) 
    is_active = Column(Boolean, default=True)