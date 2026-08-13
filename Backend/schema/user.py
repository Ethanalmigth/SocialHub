from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

class UserCreate(BaseModel):
    name: str=Field(min_length=1,max_length=50)
    email: EmailStr
    password: str=Field(min_length=8,max_length=50)

    @field_validator("password")
    @classmethod
    def check_password(cls,v):
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digits")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letters ")
        return v


class Userout(BaseModel):
    id: UUID
    name: str=Field(min_length=1,max_length=50)
    email: EmailStr
    token: str
    refresh_token: str

class Userlogin(BaseModel):
    email: EmailStr
    password: str= Field(min_length=1, max_length=100)


