# models/user_reseau.py
import typing
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.engine import Base
if typing.TYPE_CHECKING:
    from model import Reseaux
    from model import User


class UserReseau(Base):
    __tablename__ = "user_reseau"
    __table_args__ = (UniqueConstraint("user_id", "reseaux_id", name="uq_user_reseau"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    reseaux_id: Mapped[int] = mapped_column(ForeignKey("reseaux.id"), nullable=False, index=True)

    # Identité côté réseau social (ex: LinkedIn "sub", ou équivalent Twitter/autre)
    external_user_id: Mapped[str] = mapped_column(String, nullable=False)

    # Identifiant formaté pour les appels API de publication (ex: "urn:li:person:xxx")
    author_urn: Mapped[str] = mapped_column(String, nullable=False)

    # Credentials OAuth du réseau (à chiffrer, voir plus bas)
    access_token: Mapped[str] = mapped_column(String, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(String, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="reseaux_accounts")
    reseaux: Mapped["Reseaux"] = relationship("Reseaux", back_populates="user_accounts")