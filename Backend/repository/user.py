from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exception import CustomException
from model.user import User
from schema.user import UserCreate
from utils.hash import hash_password


class UserRepository:
    def __init__(self,db: AsyncSession):
        self.db = db

    async def get_user_by_email(self,email):
        results = await self.db.execute(select(User).where(User.email == email))
        user = results.scalar_one_or_none()
        return user

    async def get_user_by_id(self,user_id):
        results = await self.db.execute(select(User).where(User.id == user_id))
        user = results.scalar_one_or_none()
        return user

    async def create_user(self,user_data: UserCreate):
            user =User(email = user_data.email,name = user_data.name,hashed_password = hash_password(user_data.password))
            self.db.add(user)
            await self.db.flush()
            return user

