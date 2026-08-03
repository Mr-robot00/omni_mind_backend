from pydantic import BaseModel

class VaultItemCreate(BaseModel):
    title: str
    secret_content: str


class VaultItemResponse(BaseModel):
    id:int
    title:str
    secret_content:str
    user_id:int

    class Config:
        from_attributes = True
