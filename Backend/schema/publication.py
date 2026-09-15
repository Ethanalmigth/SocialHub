from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from enums.status_publication import StatusPublication


class PublicationCreate(BaseModel):
    post_id: UUID
    reseaux_id: int
    schedule_at: datetime

class PublicationResponse(BaseModel):
    id: UUID
    reseaux_id: int
    post_id: UUID
    created_at: datetime
    published_at: datetime | None= None
    schedule_at: datetime
    status: StatusPublication
