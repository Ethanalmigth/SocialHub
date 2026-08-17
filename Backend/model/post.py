import typing
import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import String, DateTime, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.engine import Base
if typing.TYPE_CHECKING:
   from .user import User
   from .publication import Publication

class Post(Base):
    __tablename__ = "post"
    id: Mapped[uuid.UUID]= mapped_column(Uuid,primary_key=True,default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(100),nullable=False,index=True)
    content: Mapped[str] = mapped_column(String,nullable=False)
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False, server_default=func.now())
    updated_at: Mapped[datetime]= mapped_column(DateTime(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())
    user_id:Mapped[UUID]= mapped_column(ForeignKey("user.id"),nullable=False,index=True)
    user: Mapped["User"]= relationship("User",back_populates="posts")
    publications:Mapped[list["Publication"]]= relationship("Publication",back_populates="post")