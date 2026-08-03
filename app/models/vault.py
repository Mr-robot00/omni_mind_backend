from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class DBVaultItem(Base):
    __tablename__ = "vault_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    secret_content = Column(String)

    user_id = Column(Integer, ForeignKey("user.id" , ondelete='CASCADE'))
    owner = relationship("DBUser", back_populates= "vault_items")

