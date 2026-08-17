from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PostCreate(BaseModel):
      title: str
      content: str

class PostResponse(BaseModel):
      id: UUID
      user_id: UUID
      title: str
      content: str
      created_at: datetime
      updated_at: datetime