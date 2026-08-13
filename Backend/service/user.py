from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from core.exception import CustomException
from core.setting import settings

from repository.refreshToken import RefreshTokenRepository
from repository.user import UserRepository
from schema.user import Userout, Userlogin
from utils.hash import verify_password
from utils.token import create_token, create_refresh_token, verify_token


class UserService:
    def __init__(self, db:AsyncSession):
        self.repo=UserRepository(db)
        self.repoToken=RefreshTokenRepository(db)

    async def register_user(self, user):
        user_exist= await self.repo.get_user_by_email(user.email)
        if user_exist:
            raise CustomException(status_code=status.HTTP_409_CONFLICT,message="User already exist with this email")

        user_created= await self.repo.create_user(user)
        token_data={"id":str(user_created.id),"email":user_created.email,"name":user_created.name}
        token = create_token(token_data)
        expire= datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRES)
        refreshToken = create_refresh_token(token_data,expire)
        await self.repoToken.delete_refresh_token_by_user_id(user_created.id)
        await self.repoToken.register_refresh_token(refreshToken,user_created.id,expire)
        return Userout(id=str(user_created.id),email=user_created.email,name=user_created.name,token=token,refresh_token=refreshToken)



    async def login_user(self,user:Userlogin):
        user_exist= await self.repo.get_user_by_email(user.email)
        if not user_exist:
            raise CustomException(status_code=status.HTTP_404_NOT_FOUND,message="User does not exist")
        if not verify_password(user.password,user_exist.password):
            raise CustomException(status_code=status.HTTP_401_UNAUTHORIZED,message="Incorrect Password")
        token_data={"id":str(user_exist.id),"email":user_exist.email,"name":user_exist.name}
        token = create_token(token_data)
        expire=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRES)
        refreshtoken = create_refresh_token(token_data,expire)
        await self.repoToken.delete_refresh_token_by_user_id(user_exist.id)
        await self.repoToken.register_refresh_token(refreshtoken,user_exist.id,expire)
        return Userout(id=str(user_exist.id),email=user_exist.email,name=user_exist.name,token=token,refresh_token=refreshtoken)



    async def refresh(self,refresh_token:str):
        payload= verify_token(refresh_token,"refresh")
        token_db= await self.repoToken.get_refresh_token_by_token(refresh_token)
        if not token_db:
            raise CustomException(status_code=status.HTTP_404_NOT_FOUND,message="No refresh token found")

        if  token_db.revoked:
            await self.repoToken.delete_refresh_token(refresh_token)
            raise CustomException(status_code=status.HTTP_401_UNAUTHORIZED,message="Refresh Token revoke")

        if token_db.expire_at<datetime.now(timezone.utc):
            await self.repoToken.delete_refresh_token(refresh_token)
            raise CustomException(status_code=status.HTTP_401_UNAUTHORIZED,message="Token expired")

        data_token={"id":payload["id"],"email":payload["email"],"name":payload["name"]}
        token = create_token(data_token)
        expire=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRES)
        refreshtoken = create_refresh_token(data_token,expire)
        await self.repoToken.delete_refresh_token(refresh_token)
        await self.repoToken.register_refresh_token(refreshtoken,payload["id"],expire)
        return Userout(id=str(payload["id"]),email=payload["email"],name=payload["name"],token=token,refresh_token=refreshtoken)



    async def logout(self,id_user:UUID):
        await self.repoToken.delete_refresh_token_by_user_id(id_user)
        return None


