from pydantic import BaseModel

class PostCreate(BaseModel):
      title: str
      description: str

class PostResponse(BaseModel):
      id: int
      title: str
      description: str