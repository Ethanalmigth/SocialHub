import uuid
from datetime import datetime

from sqlalchemy import Uuid, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from core.engine import Base
from .user import User


class RefreshToken(Base):
    __tablename__ = 'refresh_token'
    id:Mapped[uuid.UUID]= mapped_column(Uuid,primary_key=True,default=uuid.uuid4)
    token:Mapped[str]= mapped_column(String,nullable=False,unique=True,index=True)
    user_id:Mapped[uuid.UUID]= mapped_column(ForeignKey('user.id'),nullable=False,index=True,unique=True)
    revoked:Mapped[bool]=mapped_column(Boolean,default=False,nullable=False)
    expire_at:Mapped[datetime]= mapped_column(DateTime(timezone=True),nullable=False,index=True)
