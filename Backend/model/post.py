from sqlalchemy import Column, String, Integer, DateTime
from core.engine import Base

class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)