import uuid

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils import EmailType

from core.engine import Base
class User(Base):
    __tablename__ = "user"
    id:Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True,default=uuid.uuid4)
    name: Mapped[str]= mapped_column(String,nullable=False)
    email: Mapped[str]= mapped_column(EmailType,nullable=False,unique=True)
    password: Mapped[str]= mapped_column(String,nullable=False)