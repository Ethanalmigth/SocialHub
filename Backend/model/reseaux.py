import typing

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.engine import Base

if typing.TYPE_CHECKING:
    from .post import Post
    from .publication import Publication
    from .user_reseau import UserReseau

class Reseaux(Base):
    __tablename__ = "reseaux"
    id:Mapped[int] = mapped_column(Integer,primary_key=True)
    name:Mapped[str] = mapped_column(String,nullable=False,unique=True)
    max_characters:Mapped[int] = mapped_column(Integer,nullable=False)
    api_base_url:Mapped[str] = mapped_column(String,nullable=False,unique=True)
    publications:Mapped[list["Publication"]] = relationship("Publication",back_populates="reseaux")
    reseaux_accounts = relationship("UserReseau", back_populates="reseau")
