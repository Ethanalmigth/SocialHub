from typing import TypeVar,Generic

from pydantic import BaseModel

T = TypeVar('T')


class ReponseAPI(BaseModel,Generic[T]):
    success: bool
    message: str
    data: T|None=None