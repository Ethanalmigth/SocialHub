from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exception import CustomException
from model.user import User
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

    async def create_user(self,user: User):
        try:
            user =User(email = user.email,name = user.name,hashed_password = hash_password(user.password))
            self.db.add(user)
            return user
        except Exception as e:
            await self.db.rollback()
            raise CustomException(status_code=400,message=str(e))
