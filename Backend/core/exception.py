from typing import Optional

from starlette import status


class CustomException(Exception):
    def __init__(self, status_code:int=status.HTTP_400_BAD_REQUEST, message:Optional[str]=None):
        self.status_code = status_code
        self.message = message
        super().__init__(message)