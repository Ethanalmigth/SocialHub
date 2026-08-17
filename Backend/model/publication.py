import typing
from datetime import datetime
from uuid import UUID
from sqlalchemy import Integer, ForeignKey, DateTime, func, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.engine import Base
from enums.status_publication import StatusPublication

if typing.TYPE_CHECKING:
    from .post import Post
    from .reseaux import Reseaux



class Publication(Base):
    __tablename__ = 'publication'
    __table_args__ = (UniqueConstraint("post_id", "reseaux_id", name="uq_post_reseau"),)
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    post_id:Mapped[UUID]=mapped_column(ForeignKey("post.id"),nullable=False,index=True)
    reseaux_id:Mapped[int]=mapped_column(ForeignKey("reseaux.id"),nullable=False,index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    schedule_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at:Mapped[datetime| None]=mapped_column(DateTime(timezone=True),nullable=True)
    status:Mapped[StatusPublication]=mapped_column(Enum(StatusPublication), nullable=False, default=StatusPublication.PENDING)
    post:Mapped["Post"]=relationship("Post",back_populates="publications")
    reseaux:Mapped["Reseaux"]=relationship("Reseaux",back_populates="publications")
