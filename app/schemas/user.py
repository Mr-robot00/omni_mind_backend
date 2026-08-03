from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    is_active: bool = True

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str